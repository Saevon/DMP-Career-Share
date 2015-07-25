import some_other_module


def merge_rnd(difficulty, init_science, cur_science, server_science,
              init_reports, cur_reports, server_reports,
              init_techs, cur_techs, server_techs):
    merged_reports = merge_reports(cur_reports, server_reports)
    merged_techs = merge_techs(cur_techs, server_techs)
    merged_science = merge_science(
        difficulty, init_science, cur_science, server_science,
        init_reports, cur_reports, server_reports, merged_reports,
        init_techs, cur_techs, server_techs, merged_techs
    )

    update_rnd(merged_science, merged_techs, merged_reports)


def merge_diff(init, cur, server):
    return server - (init - cur)


def merge_funds(init_funds, cur_funds, server_funds):
    return merge_diff(init_funds, cur_funds, server_funds)


def merge_reputation(init_rep, cur_rep, server_rep):
    return merge_diff(init_rep, cur_rep, server_rep)


# Science merging

def merge_reports(cur_reports, server_reports):
    """
    Merges reports based on report_id
    Expects two dictionaries of reports where each report is a dictionary
    """
    for report_id, report in cur_reports.iter_items():
        server_reports[report_id] = merge_sci(
            report,
            server_reports[report_id]
        )

    return server_reports


def merge_science(difficulty, init_science, cur_science, server_science,
                  init_reports, cur_reports, server_reports, merged_reports,
                  init_techs, cur_techs, server_techs, merged_techs):
    # Deltas are guaranteed to be positive
    # Server deltas are the amount the server files will change by
    # Normal deltas are local changes
    server_report_delta = (calc_report_science(merged_reports, difficulty) -
                           calc_report_science(server_reports, difficulty))
    report_delta = (calc_report_science(cur_reports, difficulty) -
                    calc_report_science(init_reports, difficulty))
    server_tech_delta = (calc_tech_cost(merged_techs) -
                         calc_tech_cost(server_techs))
    tech_delta = calc_tech_cost(cur_techs) - calc_tech_cost(init_techs)

    # Any duplicated techs will be refunded by adding the cost back to the science pool
    duplicated_tech = tech_delta - server_tech_delta
    contract_delta = cur_science - init_science - report_delta + tech_delta

    return (server_science + server_report_delta -
            server_tech_delta + contract_delta + duplicated_tech)


def calc_report_science(reports, difficulty=1):
    return sum(report['sci'] for report in reports) * difficulty


def calc_tech_cost(techs):
    return sum(tech['cost'] for tech in techs)


def merge_sci(cur_report, server_report):
    """
    Merges individual science report
    sci - science achieved
    cap - science cap
    scv - decaying multiplier (science value)
    scv = (cap - sci) / cap
    """
    if not server_report:
        return cur_report

    # Just add the total science values and make sure its <= cap
    server_report['sci'] = min(
        cur_report['sci'] + server_report['sci'],
        server_report['cap']
    )
    server_report['scv'] = (
        (server_report['cap'] - server_report['sci']) / server_report['cap']
    )

    return server_report


def merge_techs(cur_techs, server_techs):
    """
    Simply merges the two dictionaries of techs
    """
    server_techs.update(cur_techs)
    return server_techs


def update_rnd(merged_science, merged_techs, merged_reports):
    """
    Writes to RnD file with updated values
    """
    pass
