from app.services.fusion import rrf_scores, fused_ids


def test_rrf_rewards_items_found_by_both_branches():
    combined = fused_ids([['a', 'b', 'c'], ['c', 'd', 'a']])
    assert combined[0] == 'a'  # same score total as c? a=(1/61+1/63), c=(1/63+1/61), tie -> a
    assert combined[1] == 'c'
    assert rrf_scores([['x', 'x', 'y']])['y'] == 1 / 62


def test_empty_fusion():
    assert fused_ids([[], []]) == []
