"""Deterministic cross-request constraint propagation; no state inference."""
from collections import defaultdict

from .core import category_for, deletion_intent


TYPES = {
    ('account_service', 'USER_PROFILE'): 'primary_account',
    ('analytics_platform', 'ANALYTICS_PROFILE'): 'analytics_profile',
    ('security_service', 'SECURITY_AUDIT_LOG'): 'security_audit_record',
}


def request_key(request, identities):
    cutoff = request['audit_at']
    return (identities.resolve(request['email']), request.get('requested_at', ''),
            min(request.get('reported_at', cutoff), cutoff))


def resource_type(resource):
    system, identifier = resource
    return TYPES.get((system, category_for(identifier)))


def eliminate(candidates, grounded, trace=None):
    """Slots are (episode, type). Grounded slots may have multiple proven
    records. Singleton proposals are simultaneous; contested singletons never
    win by iteration order. Returns assignments and unresolved candidate sets."""
    trace = trace if trace is not None else []
    ground_claims = defaultdict(set)
    for slot, resources in grounded.items():
        for resource in resources:
            ground_claims[resource].add(slot)
    conflicted = {resource for resource, slots in ground_claims.items() if len(slots) > 1}
    conflicting_primary = {slot for slot, resources in grounded.items()
                           if slot[1] == 'primary_account' and len(resources) > 1}
    assigned = {slot: set(resources)-conflicted for slot, resources in grounded.items()
                if set(resources)-conflicted and slot not in conflicting_primary}
    remaining = {slot: set(resources) for slot, resources in candidates.items()}
    for slot in conflicting_primary:
        remaining.setdefault(slot,set()).update(grounded[slot])
    for resource in conflicted:
        for slot in ground_claims[resource]:
            remaining.setdefault(slot,set()).add(resource)
    while True:
        taken = set().union(*assigned.values()) if assigned else set()
        proposals = defaultdict(list)
        for slot in sorted(remaining):
            if slot in assigned:
                continue
            removed = remaining[slot] & taken
            remaining[slot] -= taken
            if removed:
                trace.append(dict(action='remove_assigned', slot=slot, resources=sorted(removed)))
            if len(remaining[slot]) == 1:
                proposals[next(iter(remaining[slot]))].append(slot)
        additions = {slots[0]: {resource} for resource, slots in proposals.items() if len(slots) == 1}
        if not additions:
            for resource, slots in sorted(proposals.items()):
                trace.append(dict(action='contested_singleton', resource=resource, slots=sorted(slots)))
            trace.append(dict(action='fixed_point', unresolved=[dict(slot=s,resources=sorted(rs))
                              for s,rs in sorted(remaining.items()) if s not in assigned and rs]))
            break
        for slot, resources in sorted(additions.items()):
            trace.append(dict(action='assign_unique', slot=slot, resources=sorted(resources)))
        assigned.update(additions)
    unresolved = {slot: resources for slot, resources in remaining.items()
                  if slot not in assigned and resources}
    return assigned, unresolved


def build(engine, requests, extended=False):
    # Repeated audits of overlapping intake windows for the same subject are
    # one episode, not competing people. No input ordering affects grouping.
    windows = {}
    for request in requests:
        if not deletion_intent(request['request_text']):
            continue
        try:
            key = request_key(request, engine.identities)
        except ValueError:
            continue
        windows[key] = max(windows.get(key, ''), request['audit_at'])
    by_subject = defaultdict(list)
    for key in sorted(windows):
        by_subject[key[0]].append(key)
    episodes = []
    membership = {}
    for subject in sorted(by_subject):
        groups = []
        for key in by_subject[subject]:
            if groups and key[1] <= groups[-1]['end']:
                group = groups[-1]
                group['end'] = max(group['end'], key[2])
                group['cutoff'] = max(group['cutoff'], windows[key])
                group['members'].append(key)
            else:
                groups.append(dict(subject=subject, start=key[1], end=key[2],
                                   cutoff=windows[key], members=[key]))
        for group in groups:
            episode = (subject, group['start'], group['end'])
            group['key'] = episode
            episodes.append(group)
            for member in group['members']:
                membership[member] = episode

    direct_owners = {resource: {u for u, _, _ in links}
                     for resource, links in engine.resource_links.items()}
    candidates = defaultdict(set)
    grounded = defaultdict(set)
    trace = []
    for group in episodes:
        subject = group['subject']
        for resource, links in sorted(engine.resource_links.items()):
            kind = resource_type(resource)
            if not kind or direct_owners[resource] != {subject}:
                continue
            if any(group['start'] <= obs.time <= group['cutoff']
                   for obs in engine.by_resource.get(resource, ())):
                grounded[(group['key'], kind)].add(resource)
                trace.append(dict(action='grounded_lock', slot=(group['key'],kind), resource=resource,
                                  sources=[dict(subject=u,available=t,evidence_id=e) for u,t,e in sorted(links)]))
        for event in engine.activities:
            if event['source_system'] != 'deletion_worker':
                continue
            if not group['start'] <= event['event_time'] <= (group['cutoff'] if extended else group['end']):
                continue
            resource = event['target_system'], event['resource_id']
            kind = resource_type(resource)
            if not kind:
                continue
            slot = group['key'], kind
            owners = direct_owners.get(resource, set())
            if owners:
                if owners == {subject}:
                    grounded[slot].add(resource)
                trace.append(dict(action='direct_owner_filter',slot=slot,resource=resource,
                                  owners=sorted(owners),evidence_ids=sorted({e for _,_,e in engine.resource_links[resource]})))
                # Explicit ownership removes the resource from everyone else.
                continue
            candidates[slot].add(resource)
    assigned, unresolved = eliminate(candidates, grounded, trace)
    return dict(membership=membership, assigned=assigned, unresolved=unresolved,
                candidates=dict(candidates), grounded=dict(grounded), trace=trace)


def resolved_for(result, request, identities):
    key = request_key(request, identities)
    episode = result['membership'].get(key)
    resources = set()
    for (owner_episode, _), assigned in result['assigned'].items():
        if owner_episode == episode:
            resources.update(assigned)
    return resources
