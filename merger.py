#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import OrderedDict
from decimal import Decimal
from parser_data import DuplicationList

from error import DMPException


DIFFICULTY = Decimal(0.7)

class MergeException(DMPException):
    pass

def merge(initial, current, server):
    '''
    Merges as a three way diff, updating all three to the new value
    '''

    try:
        _merge(initial, current, server)
    except Exception as err:
        raise MergeException.wrap(err)


def _merge(initial, current, server):

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

    sci_refund, new_techs = merge_techs(
        initial["ResearchAndDevelopment.txt"].data["Tech"],
        current["ResearchAndDevelopment.txt"].data["Tech"],
        server["ResearchAndDevelopment.txt"].data["Tech"],
    )
    # TODO: If two people buy tech, you paid for it twice
    #     If we can figure out how much to refund...
    fund_refund = 0

    # Tech sci is an expenditure, thus difficulty doesn't apply
    new_sci += sci_refund

    sci_refund, new_reports = merge_reports(
        initial["ResearchAndDevelopment.txt"].data["Science"],
        current["ResearchAndDevelopment.txt"].data["Science"],
        server["ResearchAndDevelopment.txt"].data["Science"],
    )

    # RnD sci is a reward, thus difficulty applies
    new_sci += (sci_refund * DIFFICULTY)

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
    new_lvls = merge_building_upgrades(
        initial["ScenarioUpgradeableFacilities.txt"].data,
        current["ScenarioUpgradeableFacilities.txt"].data,
        server["ScenarioUpgradeableFacilities.txt"].data,
    )
    for building, lvl in new_lvls:
        initial["ScenarioUpgradeableFacilities.txt"].data[building]["lvl"] = lvl
        current["ScenarioUpgradeableFacilities.txt"].data[building]["lvl"] = lvl
        server["ScenarioUpgradeableFacilities.txt"].data[building]["lvl"] = lvl

    # TODO: Fixing a building that was fixed is a refund, should be added
    new_status = merge_building_status(
        initial["ScenarioDestructibles.txt"].data,
        current["ScenarioDestructibles.txt"].data,
        server["ScenarioDestructibles.txt"].data,
    )
    for building, status in new_status:
        initial["ScenarioDestructibles.txt"].data[building]["intact"] = status
        current["ScenarioDestructibles.txt"].data[building]["intact"] = status
        server["ScenarioDestructibles.txt"].data[building]["intact"] = status



#########################################################################################################################
# Buildings
#########################################################################################################################

def merge_building_upgrades(initial, current, server):
    buildings = OrderedDict()

    for key in initial.keys():
        # Ignore non-building keys
        if not isinstance(initial[key], dict):
            continue
        if initial[key].get('lvl', None) is None:
            continue

        if current[key]["lvl"] != initial[key]["lvl"]:
            # User upgraded
            if initial[key]["lvl"] != server[key]["lvl"]:
                print "WARNING: Player upgraded %(key)s (%(initial)s >> %(current)s) server upgraded (%(initial)s >> %(server)s)" % {
                    'key': key,
                    'initial': initial[key]["lvl"],
                    'current': current[key]["lvl"],
                    'server': server[key]["lvl"],
                }

            buildings[key] = max(current[key]["lvl"], server[key]["lvl"])
        else:
            # Nothing changed, use the server value
            buildings[key] = server[key]["lvl"]

    return buildings



def merge_building_status(initial, current, server):
    buildings = OrderedDict()

    for key in initial.keys():
        # Ignore non-building keys
        if not isinstance(initial[key], dict):
            continue
        if initial[key].get('intact', None) is None:
            continue

        if current[key]["intact"] != initial[key]["intact"]:
            if initial[key]["intact"] != server[key]["intact"]:
                if not initial[key]["intact"]:
                    # Both server and player fixes something
                    print "WARNING: Player and Server fixed: %s" % key

                    buildings[key] = True
                else:
                    # Both serer and player broke something
                    buildings[key] = False
            else:
                # Sever did nothing, keep the player value
                buildings[key] = current[key]["intact"]
        else:
            # Player did nothing, keep the server value
            buildings[key] = server[key]["intact"]

    return buildings






#########################################################################################################################
# Simple Stats: Funds, Rep, Sci
#########################################################################################################################

def merge_diff(init, cur, server):
    return server - (init - cur)


def merge_funds(init_funds, cur_funds, server_funds):
    return merge_diff(init_funds, cur_funds, server_funds)


def merge_reputation(init_rep, cur_rep, server_rep):
    return merge_diff(init_rep, cur_rep, server_rep)





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
        (initial, 'initial'),
        (current, 'current'),
        (server, 'server'),
    )
    for data, key in mapping:
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
    report_map, all_reports = list_to_map(initial, current, server)

    # Now merge each report
    total_refund = 0
    new_reports = DuplicationList()
    for report in all_reports:
        refund, new_report = merge_report(
            report_map.get("initial", None)[report],
            report_map.get("current", None)[report],
            report_map.get("server", None)[report],
        )
        total_refund += refund

        new_reports.append(new_report)

    return total_refund, new_reports

def round_length(val, lenght):
    val = str(val)
    if len(val) > lenght:
        val = val[:lenght]
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
    refund = 0
    if not server:
        # Server didn't do this, keep current
        return refund, current

    if not current:
        # User didn't do this, keep server
        return refund, server

    new_report = OrderedDict()
    new_report.update(server)

    # Calculate the amount the user gained
    initial_sci = initial['sci'] if initial is not None else Decimal(0)
    diff_sci = initial_sci - current['sci']

    # Add the user's sci to the server, remembering to refund extra sci
    new_report['sci'] = diff_sci + server['sci']
    if new_report['sci'] > server['cap']:
        refund = server['cap'] - new_report['sci']
        new_report['sci'] = min(
            new_report,
            server['cap']
        )

    # Update the Data Value to reflect the new percent Done
    new_report['scv'] = round_length(
        (new_report['cap'] - new_report['sci']) / new_report['cap'],
        12,
    )

    return refund, new_report


def merge_techs(initial, current, server):
    '''
    Merges all researched tech.
    Returns the refund that should be applied, and a new techs list to replace the old one
    '''
    tech_map, all_techs = list_to_map(initial, current, server)

    # Now merge each tech
    total_refund = 0
    new_techs = DuplicationList()
    for tech in all_techs:
        refund, new_tech = merge_tech(
            tech_map.get("initial", None)[tech],
            tech_map.get("current", None)[tech],
            tech_map.get("server", None)[tech],
        )
        total_refund += refund

        new_techs.append(new_tech)

    return total_refund, new_techs


def merge_tech(initial, current, server):
    '''
    Merges an individual researched tech.
    Returns the refund that should be applied, and a new tech object to replace the old one
    '''
    sci_refund = 0

    if server is None:
        # The server did nothing, keep the player's
        return current

    if current is None:
        # The player did nothing, keep the server's
        return server

    if initial is None:
        # Both server and player researched this
        sci_refund = current["cost"]

    new_tech = OrderedDict()
    new_tech.update(current)
    new_tech["part"] = DuplicationList()

    # Start with the all the parts of the server
    for part in server["part"]:
        new_tech["part"].append(part)

    # See what the player changed
    for part in current["part"]:
        if initial is not None and part in initial["part"]:
            continue
        if part in new_tech["part"]:
            print "WARNING: Both server and player bought part: %s" % part
        new_tech["part"].append(part)


    if new_tech["state"] != "Available":
        print "WARNING: tech state is not Available? WTF does that mean?"

    return sci_refund, new_tech


