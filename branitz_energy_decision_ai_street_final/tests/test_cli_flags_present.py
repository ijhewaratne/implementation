def test_integrate_cli_flags_present():
    import integrate_npv_with_dh_system as cli
    p = cli.build_parser()
    flags = {a.option_strings[0] for a in p._actions if a.option_strings}
    for need in ["--optimize-dn","--catalog","--out-dir","--report-html","--export-geojson","--monte-carlo"]:
        assert need in flags

def test_simulator_cli_flags_present():
    from street_final_copy_3.simulate_dual_pipe_dh_network_final import build_parser
    p = build_parser()
    flags = {a.option_strings[0] for a in p._actions if a.option_strings}
    for need in ["--optimize-dn","--catalog","--out-dir","--report-html","--export-geojson","--monte-carlo"]:
        assert need in flags 