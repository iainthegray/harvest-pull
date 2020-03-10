#!/usr/bin/env python3

import requests
import pprint
from datetime import date as d
from datetime import timedelta as td
from datetime import datetime as dt
from texttable import Texttable
import os

#  Script takes 2 OS environment vars
try:
    acc_id = os.environ['HARVEST_ACC_ID']
except KeyError:
    print("set harvest account ID as env var HARVEST_ACC_ID")
    exit(1)

try:
    auth = os.environ['HARVEST_AUTH_KEY']
except KeyError:
    print("set harvest auth token as HARVEST_AUTH_KEY")
    exit(1)

# acc_id = "119xxx"
# auth="2221695.pt.xxx"
def numOfDays(date1, date2):
    return (date2-date1).days

pp = pprint.PrettyPrinter(indent=2)
t = Texttable()
t.add_row(["Customer","Start Date", "End Date", "Days Used", "Days Remaining", "% Complete", "% Used", "Status"])
right_now           = d.today()
one_year = right_now - td(days=365)


headers = {'Harvest-Account-Id': acc_id,
           'Authorization': "Bearer " + auth,
           'User-Agent': "Harvest API"}

url = "https://api.harvestapp.com/api/v2/projects"
r = requests.get(url, headers=headers)
my_proj = r.json()

url = "https://api.harvestapp.com/api/v2/reports/project_budget"
r = requests.get(url, headers=headers)
my_budg = r.json()

url = "https://api.harvestapp.com/api/v2/reports/time/projects?from=" + one_year.strftime("%Y%m%d") + "&to=" + right_now.strftime("%Y%m%d")
r = requests.get(url, headers=headers)
my_bill = r.json()
# pp.pprint(my_bill)


#  Data structure
# projects = [{ my_proj[id]: { name:, start_date:,
                             # end_date:, perc_through:, tot_days:, days_rem: days_used:, perc_complete:}, {}]

projects ={}

for proj in my_proj['projects']:
    # Remove the TAM assist and Q2E as I do not own this project
    if proj['client']['name'] == 'HashiCorp' or proj['id'] == 23921242:
        continue
    print("{} - {}".format(proj['client']['name'], proj['id']))
    try:
        (s_yr, s_mn, s_dy)  = proj['starts_on'].split('-')
        start_date          = d(int(s_yr), int(s_mn), int(s_dy))
    except AttributeError as e:
        print("{} - {} has no start date".format(proj['client']['name'], proj['id']))
        continue
    try:
        (e_yr, e_mn, e_dy)  = proj['ends_on'].split('-')
        end_date            = d(int(e_yr), int(e_mn), int(e_dy))
    except AttributeError as e:
        print("{} - {} has no start date".format(proj['client']['name'], proj['id']))
        continue
    total_days          = numOfDays(start_date, end_date)
    days_through        = numOfDays(start_date, right_now)
    perc_through        = (days_through / total_days) * 100
    print('{}: {} days used {}%'.format(proj['name'], days_through, "{:.0f}".format(perc_through)) )
    projects[proj['id']]                = {}
    projects[proj['id']]['name']        = proj['name']
    projects[proj['id']]['start_date']  = start_date.strftime("%d-%m-%Y")
    projects[proj['id']]['end_date']    = end_date.strftime("%d-%m-%Y")
    projects[proj['id']]['perc_days']   = "{:.0f}".format(perc_through)

for budg in my_budg['results']:
    # Remove the TAM assist and Q2E as I do not own this project
    if budg['client_name'] == 'HashiCorp' or budg['project_id'] == 23921242:
        continue
    try:
        projects[budg['project_id']]['tot_days']    = "{:.0f}".format(budg['budget'] / 8)
    except KeyError as e:
        print('{} Not added yet'.format(budg['project_id']))
        continue

    projects[budg['project_id']]['days_rem']    = "{:.1f}".format(budg['budget_remaining'] / 8)
    projects[budg['project_id']]['days_used']    = "{:.1f}".format((budg['budget'] - budg['budget_remaining']) / 8)

for bill in my_bill['results']:
    # Remove the TAM assist as I do not own this project
    if bill['client_name'] == 'HashiCorp' or bill['project_id'] == 23921242:
        continue
    print("{} - {}".format(bill['project_name'], bill['project_id']))
    projects[bill['project_id']]['days_billed'] \
        = "{:.1f}".format(bill['billable_hours'] / 8)
    projects[bill['project_id']]['days_non_billed'] \
        = "{:.1f}".format((bill['billable_hours'] - bill['total_hours']) / 8)
    projects[bill['project_id']]['perc_comp'] \
        = "{:.1f}".format((float(projects[bill['project_id']]['days_billed']) / float(projects[bill['project_id']]['tot_days'])) * 100)

for pr in projects:
    if 'perc_comp' not in projects[pr].keys():
        projects[pr]['perc_comp'] = 0

    if (float(projects[pr]['perc_days']) - float(projects[pr]['perc_comp'])) <= 15:
        projects[pr]['status'] = "Green"
    elif (float(projects[pr]['perc_days']) - float(projects[pr]['perc_comp'])) <= 40:
        projects[pr]['status'] = "Amber"
    else:
        projects[pr]['status'] = "Red"

    t.add_row(  [
                    projects[pr]['name'],
                    projects[pr]['start_date'],
                    projects[pr]['end_date'],
                    projects[pr]['days_used'],
                    projects[pr]['days_rem'],
                    projects[pr]['perc_days'],
                    projects[pr]['perc_comp'],
                    projects[pr]['status']
                ]
            )

print(t.draw())

# pp.pprint(projects)
