#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import OrderedDict
from decimal import Decimal
from parser_data import DuplicationList

from error import DMPException


DIFFICULTY = Decimal(0.7)



warnings = []


class MergeException(DMPException):
    pass

def merge(initial, current, server):
    '''
    Merges as a three way diff, updating all three to the new value
    '''

    try:
        return _merge(initial, current, server)
    except Exception as err:
        raise MergeException.wrap(err)


def _merge(initial, current, server):
    errors = []

    #########################################
    # Funds
    new_funds = merge_diff(
        initial["Funding.txt"].data["funds"],
        current["Funding.txt"].data["funds"],
        server["Funding.txt"].data["funds"],
    )

    initial["Funding.txt"].data["funds"] = new_funds
    current["Funding.txt"].data["funds"] = new_funds
    server["Funding.txt"].data["funds"] = new_funds



    #########################################
    # Reputation
    new_rep = merge_diff(
        initial["Reputation.txt"].data["rep"],
        current["Reputation.txt"].data["rep"],
        server["Reputation.txt"].data["rep"],
    )

    initial["Reputation.txt"].data["rep"] = new_rep
    current["Reputation.txt"].data["rep"] = new_rep
    server["Reputation.txt"].data["rep"] = new_rep


    #########################################
    # Science
    new_sci = merge_diff(
        initial["ResearchAndDevelopment.txt"].data["sci"],
        current["ResearchAndDevelopment.txt"].data["sci"],
        server["ResearchAndDevelopment.txt"].data["sci"],
    )

    sci_refund, new_techs, new_errors = merge_techs(
        initial["ResearchAndDevelopment.txt"].data.get("Tech", None),
        current["ResearchAndDevelopment.txt"].data.get("Tech", None),
        server["ResearchAndDevelopment.txt"].data.get("Tech", None),
    )
    errors += new_errors

    # TODO: If two people buy tech, you paid for it twice
    #     If we can figure out how much to refund...
    fund_refund = 0

    # Tech sci is an expenditure, thus difficulty doesn't apply
    new_sci += sci_refund

    sci_refund, new_reports, new_errors = merge_reports(
        initial["ResearchAndDevelopment.txt"].data.get("Science", None),
        current["ResearchAndDevelopment.txt"].data.get("Science", None),
        server["ResearchAndDevelopment.txt"].data.get("Science", None),
    )
    errors += new_errors

    # RnD sci is a reward, thus difficulty applies
    new_sci += (sci_refund * DIFFICULTY)
    new_sci = round_length(new_sci, 12)

    initial["ResearchAndDevelopment.txt"].data["Tech"] = new_techs
    current["ResearchAndDevelopment.txt"].data["Tech"] = new_techs
    server["ResearchAndDevelopment.txt"].data["Tech"] = new_techs

    initial["ResearchAndDevelopment.txt"].data["Science"] = new_reports
    current["ResearchAndDevelopment.txt"].data["Science"] = new_reports
    server["ResearchAndDevelopment.txt"].data["Science"] = new_reports

    initial["Funding.txt"].data["funds"] += fund_refund
    current["Funding.txt"].data["funds"] += fund_refund
    server["Funding.txt"].data["funds"] += fund_refund

    initial["ResearchAndDevelopment.txt"].data["sci"] = new_sci
    current["ResearchAndDevelopment.txt"].data["sci"] = new_sci
    server["ResearchAndDevelopment.txt"].data["sci"] = new_sci

    #########################################
    # Buildings

    # TODO: Upgrading a building that was upgraded is a refund, should be added
    new_lvls, new_errors = merge_building_upgrades(
        initial["ScenarioUpgradeableFacilities.txt"].data,
        current["ScenarioUpgradeableFacilities.txt"].data,
        server["ScenarioUpgradeableFacilities.txt"].data,
    )
    for building, lvl in new_lvls.iteritems():
        initial["ScenarioUpgradeableFacilities.txt"].data[building][0]["lvl"] = lvl
        current["ScenarioUpgradeableFacilities.txt"].data[building][0]["lvl"] = lvl
        server["ScenarioUpgradeableFacilities.txt"].data[building][0]["lvl"] = lvl

    errors += new_errors

    # TODO: Fixing a building that was fixed is a refund, should be added
    new_status, new_errors = merge_building_status(
        initial["ScenarioDestructibles.txt"].data,
        current["ScenarioDestructibles.txt"].data,
        server["ScenarioDestructibles.txt"].data,
    )
    for building, status in new_status.iteritems():
        add_or_save_building(initial["ScenarioDestructibles.txt"].data, building)["intact"] = status

    errors += new_errors

    return errors

def add_or_save_building(data, key):
    building = data.get(key, None)
    if not building:
        data[key] = DuplicationList()
        building = data[key]

    return building[0]


#########################################################################################################################
# Buildings
#########################################################################################################################

def get_building(val, key):
    val = val.get(key, None)
    if val is None:
        return {}
    return val[0]

def merge_building_upgrades(initial, current, server):
    buildings = OrderedDict()
    errors = []

    for key in initial.keys():
        initial_building = get_building(initial, key)
        current_building = get_building(current, key)
        server_building = get_building(server, key)

        # Ignore non-building keys
        if not isinstance(initial_building, dict):
            continue
        if initial_building.get('lvl', None) is None:
            continue

        if current_building.get("lvl", None) != initial_building.get("lvl", None):
            # User upgraded
            if initial_building.get("lvl", None) != server_building.get("lvl", None):
                # Server upgraded
                errors.append("WARNING: %(key)s Upgraded twice: player(%(initial)s >> %(current)s) server(%(initial)s >> %(server)s)" % {
                    'key': key,
                    'initial': initial_building.get("lvl", None),
                    'current': current_building.get("lvl", None),
                    'server': server_building.get("lvl", None),
                })

            buildings[key] = max(current_building.get("lvl", None), server_building.get("lvl", None))
        else:
            # Nothing changed, use the server value
            buildings[key] = server_building.get("lvl", None)

    return buildings, errors



def merge_building_status(initial, current, server):
    buildings = OrderedDict()
    errors = []

    for key in initial.keys():
        initial_building = get_building(initial, key)
        current_building = get_building(current, key)
        server_building = get_building(server, key)

        # Ignore non-building keys
        if not isinstance(initial_building, dict):
            continue
        if initial_building.get('intact', None) is None:
            continue

        if current_building.get("intact", None) != initial_building.get("intact", None):
            if initial_building.get("intact", None) != server_building.get("intact", None):
                if not initial_building.get("intact", None):
                    # Both server and player fixes something
                    errors.append("WARNING: %s: Fixed by both Player and Server" % key)

                    buildings[key] = True
                else:
                    # Both serer and player broke something
                    buildings[key] = False
            else:
                # Sever did nothing, keep the player value
                buildings[key] = current_building.get("intact", None)
        else:
            # Player did nothing, keep the server value
            buildings[key] = server_building.get("intact", None)

    return buildings, errors






#########################################################################################################################
# Simple Stats: Funds, Rep, Sci
#########################################################################################################################

def merge_diff(init, cur, server):
    return server - (init - cur)




#########################################################################################################################
# Science
#########################################################################################################################

def list_to_map(initial, current, server, id_func=None):
    if id_func is None:
        def id_func(val):
            return val['id']

    item_map = {
        'initial': {},
        'current': {},
        'server': {}
    }
    all_ids = []

    # First create a mapping for techs (for easier comparison)
    mapping = (
        (server, 'server'),
        (initial, 'initial'),
        (current, 'current'),
    )
    for data, key in mapping:
        if data is None:
            continue

        for report in data:
            id = id_func(report)
            if id not in all_ids:
                all_ids.append(id)
            item_map[key][id] = report

    return item_map, all_ids


def merge_reports(initial, current, server):
    """
    Merges reports based on report_id
    Expects two dictionaries of reports where each report is a dictionary
    """
    errors = []
    report_map, all_reports = list_to_map(initial, current, server)

    # Now merge each report
    total_refund = 0
    new_reports = DuplicationList()
    for report in all_reports:
        refund, new_report, new_errors = merge_report(
            report_map["initial"].get(report, None),
            report_map["current"].get(report, None),
            report_map["server"].get(report, None),
        )
        total_refund += refund
        errors += new_errors

        new_reports.append(new_report)

    return total_refund, new_reports, errors

def round_length(val, length):
    val = str(val)
    if len(val) > length:
        val = val[:length]
        val = val.rstrip('0').rstrip('.')
    return Decimal(val)


def merge_report(initial, current, server):
    """
    Merges individual science report
    sci - science achieved
    cap - science cap
    scv - decaying multiplier (science value)
    scv = (cap - sci) / cap

    returns the refund (negative, since we can only do the same research) and a new science report
    """
    errors = []

    refund = 0
    if not server:
        # Server didn't do this, keep current
        return refund, current, errors

    if not current:
        # User didn't do this, keep server
        return refund, server, errors

    new_report = OrderedDict()
    new_report.update(server)

    # Calculate the amount the user gained
    initial_sci = initial['sci'] if initial is not None else Decimal(0)
    diff_sci = current['sci'] - initial_sci

    # Add the user's sci to the server, remembering to refund extra sci
    new_report['sci'] = diff_sci + server['sci']
    if new_report['sci'] > server['cap']:
        refund = server['cap'] - new_report['sci']
        new_report['sci'] = min(
            new_report,
            server['cap']
        )

        errors.append("Warn: SciRefunding %s" % refund)

    # Update the Data Value to reflect the new percent Done
    new_report['scv'] = round_length(
        (new_report['cap'] - new_report['sci']) / new_report['cap'],
        12,
    )

    return refund, new_report, errors


def merge_techs(initial, current, server):
    '''
    Merges all researched tech.
    Returns the refund that should be applied, and a new techs list to replace the old one
    '''
    tech_map, all_techs = list_to_map(initial, current, server)
    errors = []

    # Now merge each tech
    total_refund = 0
    new_techs = DuplicationList()
    for tech in all_techs:
        refund, new_tech, new_errors = merge_tech(
            tech_map["initial"].get(tech, None),
            tech_map["current"].get(tech, None),
            tech_map["server"].get(tech, None),
        )
        total_refund += refund
        errors += new_errors

        new_techs.append(new_tech)

    return total_refund, new_techs, errors


def merge_tech(initial, current, server):
    '''
    Merges an individual researched tech.
    Returns the refund that should be applied, and a new tech object to replace the old one
    '''
    sci_refund = 0
    errors = []

    if server is None:
        # The server did nothing, keep the player's
        return sci_refund, current, errors

    if current is None:
        # The player did nothing, keep the server's
        return sci_refund, server, errors

    if initial is None:
        # Both server and player researched this
        sci_refund = current["cost"]

    new_tech = OrderedDict()
    new_tech.update(server)
    new_tech["part"] = DuplicationList()

    # Start with the all the parts of the server
    for part in server.get("part", []):
        new_tech["part"].append(part)

    # See what the player changed
    for part in current.get("part", []):
        if initial is not None and part in initial.get("part", []):
            continue
        if part in new_tech.get("part", []):
            errors.append("WARNING: Both server and player bought part: %s" % part)
            continue
        new_tech["part"].append(part)


    if new_tech["state"] != "Available":
        errors.append("WARNING: tech state is not Available? WTF does that mean?")

    return sci_refund, new_tech, errors


