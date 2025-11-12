from optimize.catalogs import load_pipe_catalog


def test_pipe_catalog_basic():
    cats = load_pipe_catalog("data/catalogs/pipe_catalog.csv")
    assert len(cats) > 0
    dns = [c.dn for c in cats]
    assert min(dns) >= 10 and max(dns) <= 2000
    # At least one of cost or loss should be present for some DN
    assert any(
        (c.cost_eur_per_m is not None) or (c.w_loss_w_per_m is not None) or (c.u_wpermk is not None)
        for c in cats
    )
