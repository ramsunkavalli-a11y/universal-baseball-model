"""Dated MLB record context; unknown affiliation is not a .500 observation."""

FEATURES = ['org_record_known', 'org_record_centered']


def rights_events(payload, source_year, teams):
    """Explicit acquisition/release evidence, not current embedded biographies."""
    rows = []
    for t in payload['transactions']:
        code = t.get('typeCode')
        if code not in {'CLW', 'IFA', 'SFA', 'SGN', 'TR', 'REL', 'FA'} or 'person' not in t:
            continue
        dates = [t[k][:10] for k in ['date', 'effectiveDate', 'resolutionDate'] if t.get(k)]
        if not dates:
            continue
        known = max(dates)
        if int(known[:4]) != source_year:
            # Delayed or outside-request dates are not silently assigned to this year.
            continue
        target = t.get('toTeam', {}).get('id')
        parent = teams.get((source_year, target), {}).get('parent_id')
        rows.append(dict(player_id=int(t['person']['id']), transaction_id=int(t['id']),
                         known_date=known, code=code,
                         parent_id=None if code in {'REL', 'FA'} else parent))
    return rows


def latest_rights(events, origin):
    relevant = [r for r in events if r['known_date'] <= f'{origin}-12-31']
    if not relevant:
        return None
    day = max(r['known_date'] for r in relevant)
    last = [r for r in relevant if r['known_date'] == day]
    owners = {r['parent_id'] for r in last}
    if len(owners) != 1:
        return dict(parent_id=None, known_date=day, code='conflicting same-day rights',
                    transaction_ids=[r['transaction_id'] for r in last])
    return dict(parent_id=last[0]['parent_id'], known_date=day,
                code='|'.join(sorted({r['code'] for r in last})),
                transaction_ids=[r['transaction_id'] for r in last])


def team_rows(payload, season):
    if not 2011 <= season <= 2024:
        raise ValueError('Unsupported or protected source season')
    out = {}
    for t in payload['teams']:
        if int(t['season']) != season:
            raise ValueError('Team source season mismatch')
        tid = int(t['id'])
        parent = tid if int(t['sport']['id']) == 1 else t.get('parentOrgId')
        r = dict(club=t['name'], parent_id=parent,
                 parent_name=t['name'] if int(t['sport']['id']) == 1 else t.get('parentOrgName'))
        if tid in out and out[tid] != r:
            raise ValueError('Conflicting club affiliation')
        out[tid] = r
    return out


def record_rows(payload, season):
    if not 2011 <= season <= 2024:
        raise ValueError('Unsupported or protected record season')
    out = {}
    for league in payload['records']:
        for r in league['teamRecords']:
            if int(r['season']) != season:
                raise ValueError('Standings source season mismatch')
            tid, wins, losses = int(r['team']['id']), int(r['wins']), int(r['losses'])
            gp = int(r['gamesPlayed'])
            lower, upper = (40, 75) if season == 2020 else (150, 180)
            if wins < 0 or losses < 0 or not lower <= wins + losses <= upper or not 0 <= gp - wins - losses <= 1:
                raise ValueError('Incomplete regular season standings')
            if tid in out:
                raise ValueError('Duplicate standings club')
            out[tid] = dict(wins=wins, losses=losses, games_played=gp,
                            win_pct=wins / (wins + losses))
    if len(out) != 30:
        raise ValueError('Incomplete MLB organization universe')
    return out


def context(*, origin, club_year, club_id, rostered, teams, records):
    if origin > 2024 or club_year is not None and club_year > origin:
        raise ValueError('Future organization evidence')
    t = teams.get((club_year, club_id), {})
    parent = t.get('parent_id')
    record = records.get((origin, parent))
    reason = ('known' if club_year == origin and record else
              'stale last observed club' if club_year is not None and club_year < origin else
              'affiliation or MLB standings unavailable')
    known = reason == 'known'
    return dict(org_record_known=int(known),
                org_record_centered=record['win_pct'] - .5 if known else 0.,
                context_club_year=club_year, context_club_id=club_id,
                context_club=t.get('club'), context_parent_id=parent,
                context_parent=t.get('parent_name'), context_reason=reason,
                context_basis='December 31 MLB roster' if rostered else 'Last primary batting club proxy',
                context_wins=record['wins'] if known else None,
                context_losses=record['losses'] if known else None)
