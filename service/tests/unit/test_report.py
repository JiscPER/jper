"""
Unit tests for the monthly report
"""

from octopus.modules.es.testindex import ESTestCase
from octopus.core import app
from octopus.lib import paths

from service import models, reports
from service.tests import fixtures
from service import scheduler

from copy import deepcopy
from datetime import datetime
from random import randint

import time, csv, os

REPORT_FILE = paths.rel2abs(__file__, "..", "resources", "report1.csv")
RESOURCES = paths.rel2abs(__file__, "..", "resources")
MONTHTRACKER = paths.rel2abs(__file__, "..", "resources", "monthtracker.cfg")

class TestModels(ESTestCase):
    def setUp(self):
        self.run_schedule = app.config.get("RUN_SCHEDULE")
        app.config["RUN_SCHEDULE"] = False
        self.old_reportsdir = app.config.get("REPORTSDIR")
        app.config['REPORTSDIR'] = RESOURCES

        super(TestModels, self).setUp()

    def tearDown(self):
        super(TestModels, self).tearDown()
        app.config["RUN_SCHEDULE"] = self.run_schedule
        if os.path.exists(REPORT_FILE):
            os.remove(REPORT_FILE)
        app.config['REPORTSDIR'] = self.old_reportsdir
        if os.path.exists(MONTHTRACKER):
            os.remove(MONTHTRACKER)
        for fn in os.listdir(RESOURCES):
            if fn.startswith("monthly_notifications_to_institutions_"):
                os.remove(os.path.join(RESOURCES, fn))

    def _load_data(self, notes, accounts=None):
        def random_date_in_month(month):
            mstr = str(month)
            if month < 10:
                mstr = "0" + mstr
            now = datetime.utcnow()
            year = str(now.year)
            day = randint(1, 28)
            dstr = str(day)
            if day < 10:
                dstr = "0" + dstr
            return year + "-" + mstr + "-" + dstr + "T00:00:00Z"

        accounts = {} if accounts is None else accounts
        source = fixtures.NotificationFactory.routed_notification()

        name_id_map = {}
        for uni_name, months in notes.items():
            names = [n.strip() for n in uni_name.split(",")]

            # first make (or re-use) an account for the repository
            accs = []
            for n in names:
                acc = None
                if n not in list(accounts.keys()):
                    acc = models.Account()
                    acc.repository_name = n
                    acc.save()
                else:
                    acc = accounts.get(n)

                accs.append(acc)
                name_id_map[n] = acc.id
                accounts[n] = acc

            for month, distribution in months.items():
                md = distribution.get("md")
                for i in range(md):
                    s = deepcopy(source)
                    del s["links"]
                    del s["id"]
                    rn = models.RoutedNotification(s)
                    rn.analysis_date = random_date_in_month(month)
                    rn.repositories = [acc.id for acc in accs]
                    rn.save()

                ct = distribution.get("content")
                for i in range(ct):
                    s = deepcopy(source)
                    del s["id"]
                    rn = models.RoutedNotification(s)
                    rn.analysis_date = random_date_in_month(month)
                    rn.repositories = [acc.id for acc in accs]
                    rn.save()

        return name_id_map, accounts


    def test_01_monthly_new(self):
        notes = {
            "Uni A" : {
                1 : { "md" : 1, "content" : 2, "total": 3},
                2 : { "md" : 3, "content" : 4, "total" : 7},
                3 : { "md" : 5, "content" : 6, "total" : 11}
            },
            "Uni B" : {
                1 : { "md" : 7, "content" : 8, "total" : 15 },
                2 : { "md" : 9, "content" : 10, "total" : 19 },
                3 : { "md" : 11, "content" : 12, "total" : 23 }
            },
            "Uni C" : {
                1 : { "md" : 13, "content" : 14, "total" : 27 },
                2 : { "md" : 15, "content" : 16, "total" : 31 },
                3 : { "md" : 17, "content" : 18, "total" : 35 }
            }
        }

        grand_totals = {
            1 : { "md" : 21, "content" : 24, "total" : 45 },
            2 : { "md" : 27, "content" : 30, "total" : 57 },
            3 : { "md" : 33, "content" : 36, "total" : 69 }
        }

        self._load_data(notes)

        time.sleep(10)

        now = datetime.utcnow()
        year = str(now.year)

        from_date = year + "-01-01T00:00:00Z"
        to_date = year + "-04-01T00:00:00Z"

        # run the delivery report
        reports.delivery_report(from_date, to_date, REPORT_FILE)

        # read in the csv and check it contains the right values
        seen = []
        with open(REPORT_FILE, "r") as f:
            reader = csv.reader(f)
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                seen.append(row[0])
                if row[0] not in ["Total", "Unique"]:
                    cfg = notes.get(row[0])
                    for mon, dist in cfg.items():
                        mdcol = 3*mon - 1
                        ctcol = mdcol + 1
                        totcol = mdcol + 2
                        assert int(row[mdcol]) == dist.get("md"), row[mdcol]
                        assert int(row[ctcol]) == dist.get("content"), row[ctcol]
                        assert int(row[totcol]) == dist.get("total"), row[totcol]
                else:
                    for mon, dist in grand_totals.items():
                        mdcol = 3*mon - 1
                        ctcol = mdcol + 1
                        totcol = mdcol + 2
                        assert int(row[mdcol]) == dist.get("md"), row[mdcol]
                        assert int(row[ctcol]) == dist.get("content"), row[ctcol]
                        assert int(row[totcol]) == dist.get("total"), row[totcol]

        # just check the coverage
        for k in list(notes.keys()):
            assert k in seen

        assert "Total" in seen
        assert "Unique" in seen

    def test_02_monthly_overlap_update(self):
        notes1 = {
            "Uni A" : {
                1 : { "md" : 1, "content" : 2, "total": 3},
                2 : { "md" : 3, "content" : 4, "total" : 7},
                3 : { "md" : 5, "content" : 6, "total" : 11}
            },
            "Uni B" : {
                1 : { "md" : 7, "content" : 8, "total" : 15 },
                2 : { "md" : 9, "content" : 10, "total" : 19 },
                3 : { "md" : 11, "content" : 12, "total" : 23 }
            },
            "Uni C" : {
                1 : { "md" : 13, "content" : 14, "total" : 27 },
                2 : { "md" : 15, "content" : 16, "total" : 31 },
                3 : { "md" : 17, "content" : 18, "total" : 35 }
            }
        }
        name_id_map, account_map = self._load_data(notes1)

        time.sleep(10)

        now = datetime.utcnow()
        year = str(now.year)

        from_date = year + "-01-01T00:00:00Z"
        to_date = year + "-04-01T00:00:00Z"

        # run the delivery report for the first time
        reports.delivery_report(from_date, to_date, REPORT_FILE)

        # we don't need to read the report just now, just check it's there and that we're
        # ready to move to the next stage
        assert os.path.exists(REPORT_FILE)

        notes2 = {
            "Uni A" : {
                3 : { "md" : 19, "content" : 20, "total": 50 }, # 39 + 11
                4 : { "md" : 21, "content" : 22, "total" : 43 },
                5 : { "md" : 23, "content" : 24, "total" : 47 }
            },
            "Uni B" : {
                3 : { "md" : 25, "content" : 26, "total" : 74 }, # 51 + 23
                4 : { "md" : 27, "content" : 28, "total" : 55 },
                5 : { "md" : 29, "content" : 30, "total" : 59 }
            },
            "Uni C" : {
                3 : { "md" : 31, "content" : 32, "total" : 98 }, # 63 + 35
                4 : { "md" : 33, "content" : 34, "total" : 67 },
                5 : { "md" : 35, "content" : 36, "total" : 71 }
            },
            "Uni D" : {
                3 : { "md" : 37, "content" : 38, "total" : 75 },
                4 : { "md" : 39, "content" : 40, "total" : 79 },
                5 : { "md" : 41, "content" : 42, "total" : 83 }
            }
        }

        self._load_data(notes2, account_map)

        time.sleep(10)

        now = datetime.utcnow()
        year = str(now.year)

        # note the month range is from february this time, so we expect the data from january to be preserved
        from_date = year + "-02-01T00:00:00Z"
        to_date = year + "-06-01T00:00:00Z"

        # run the delivery report for the second and final time
        reports.delivery_report(from_date, to_date, REPORT_FILE)

        # data to compare the output to
        notes_final = {
            "Uni A" : {
                1 : { "md" : 1, "content" : 2, "total": 3},
                2 : { "md" : 3, "content" : 4, "total" : 7},
                3 : { "md" : 24, "content" : 26, "total": 50 }, # 39 + 11
                4 : { "md" : 21, "content" : 22, "total" : 43 },
                5 : { "md" : 23, "content" : 24, "total" : 47 }
            },
            "Uni B" : {
                1 : { "md" : 7, "content" : 8, "total" : 15 },
                2 : { "md" : 9, "content" : 10, "total" : 19 },
                3 : { "md" : 36, "content" : 38, "total" : 74 }, # 51 + 23
                4 : { "md" : 27, "content" : 28, "total" : 55 },
                5 : { "md" : 29, "content" : 30, "total" : 59 }
            },
            "Uni C" : {
                1 : { "md" : 13, "content" : 14, "total" : 27 },
                2 : { "md" : 15, "content" : 16, "total" : 31 },
                3 : { "md" : 48, "content" : 50, "total" : 98 }, # 63 + 35
                4 : { "md" : 33, "content" : 34, "total" : 67 },
                5 : { "md" : 35, "content" : 36, "total" : 71 }
            },
            "Uni D" : {
                3 : { "md" : 37, "content" : 38, "total" : 75 },
                4 : { "md" : 39, "content" : 40, "total" : 79 },
                5 : { "md" : 41, "content" : 42, "total" : 83 }
            }
        }

        grand_totals = {
            1 : { "md" : 21, "content" : 24, "total" : 45 },
            2 : { "md" : 27, "content" : 30, "total" : 57 },
            3 : { "md" : 145, "content" : 152, "total" : 297 },
            4 : { "md" : 120, "content" : 124, "total" : 244 },
            5 : { "md" : 128, "content" : 132, "total" : 260 }
        }

        # read in the csv and check it contains the right values
        seen = []
        with open(REPORT_FILE, "r") as f:
            reader = csv.reader(f)
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                seen.append(row[0])
                if row[0] not in ["Total", "Unique"]:
                    cfg = notes_final.get(row[0])
                    for mon, dist in cfg.items():
                        mdcol = 3*mon - 1
                        ctcol = mdcol + 1
                        totcol = mdcol + 2
                        assert int(row[mdcol]) == dist.get("md"), row[mdcol]
                        assert int(row[ctcol]) == dist.get("content"), row[ctcol]
                        assert int(row[totcol]) == dist.get("total"), row[totcol]
                else:
                    for mon, dist in grand_totals.items():
                        mdcol = 3*mon - 1
                        ctcol = mdcol + 1
                        totcol = mdcol + 2
                        assert int(row[mdcol]) == dist.get("md"), row[mdcol]
                        assert int(row[ctcol]) == dist.get("content"), row[ctcol]
                        assert int(row[totcol]) == dist.get("total"), row[totcol]

        # just check the coverage
        for k in list(notes_final.keys()):
            assert k in seen

        assert "Total" in seen
        assert "Unique" in seen

    def test_03_multi_routed(self):
        notes1 = {
            "Uni A" : {
                1 : { "md" : 1, "content" : 2 },
                2 : { "md" : 3, "content" : 4 },
                3 : { "md" : 5, "content" : 6 }
            },
            "Uni B" : {
                1 : { "md" : 7, "content" : 8 },
                2 : { "md" : 9, "content" : 10 },
                3 : { "md" : 11, "content" : 12 }
            },
            "Uni C" : {
                1 : { "md" : 13, "content" : 14 },
                2 : { "md" : 15, "content" : 16 },
                3 : { "md" : 17, "content" : 18 }
            },
            "Uni A, Uni B" : {
                1 : { "md" : 19, "content" : 20 },
                2 : { "md" : 21, "content" : 22 },
                3 : { "md" : 23, "content" : 24 }
            }
        }
        name_id_map, account_map = self._load_data(notes1)

        time.sleep(10)

        now = datetime.utcnow()
        year = str(now.year)

        from_date = year + "-01-01T00:00:00Z"
        to_date = year + "-04-01T00:00:00Z"

        # run the delivery report for the first time
        reports.delivery_report(from_date, to_date, REPORT_FILE)

        # we don't need to read the report just now, just check it's there and that we're
        # ready to move to the next stage
        assert os.path.exists(REPORT_FILE)

        notes2 = {
            "Uni A" : {
                3 : { "md" : 19, "content" : 20 },
                4 : { "md" : 21, "content" : 22 },
                5 : { "md" : 23, "content" : 24 }
            },
            "Uni B" : {
                3 : { "md" : 25, "content" : 26 },
                4 : { "md" : 27, "content" : 28 },
                5 : { "md" : 29, "content" : 30 }
            },
            "Uni C" : {
                3 : { "md" : 31, "content" : 32 },
                4 : { "md" : 33, "content" : 34 },
                5 : { "md" : 35, "content" : 36 }
            },
            "Uni B, Uni C" : {
                3 : { "md" : 37, "content" : 38 },
                4 : { "md" : 39, "content" : 40 },
                5 : { "md" : 41, "content" : 42 }
            }
        }

        self._load_data(notes2, account_map)

        time.sleep(10)

        now = datetime.utcnow()
        year = str(now.year)

        # note the month range is from february this time, so we expect the data from january to be preserved
        from_date = year + "-03-01T00:00:00Z"
        to_date = year + "-06-01T00:00:00Z"

        # run the delivery report for the second and final time
        reports.delivery_report(from_date, to_date, REPORT_FILE)

        # data to compare the output to
        notes_final = {
            "Uni A" : {
                1 : { "md" : 20, "content" : 22, "total" : 42 },
                2 : { "md" : 24, "content" : 26, "total" : 50 },
                3 : { "md" : 47, "content" : 50, "total" : 97 },
                4 : { "md" : 21, "content" : 22, "total" : 43 },
                5 : { "md" : 23, "content" : 24, "total" : 47 }
            },
            "Uni B" : {
                1 : { "md" : 26, "content" : 28, "total" : 54 },
                2 : { "md" : 30, "content" : 32, "total" : 62 },
                3 : { "md" : 96, "content" : 100, "total" : 196 },
                4 : { "md" : 66, "content" : 68, "total" : 134 },
                5 : { "md" : 70, "content" : 72, "total" : 142 }
            },
            "Uni C" : {
                1 : { "md" : 13, "content" : 14, "total" : 27},
                2 : { "md" : 15, "content" : 16, "total" : 31 },
                3 : { "md" : 85, "content" : 88, "total" : 173 },
                4 : { "md" : 72, "content" : 74, "total" : 146 },
                5 : { "md" : 76, "content" : 78, "total" : 154 }
            }
        }

        grand_totals = {
            1 : { "md" : 59, "content" : 64, "total" : 123 },
            2 : { "md" : 69, "content" : 74, "total" : 143 },
            3 : { "md" : 228, "content" : 238, "total" : 466 },
            4 : { "md" : 159, "content" : 164, "total" : 323 },
            5 : { "md" : 169, "content" : 174, "total" : 343 }
        }

        unique_totals = {
            1 : { "md" : 40, "content" : 44, "total" : 84 },
            2 : { "md" : 48, "content" : 52, "total" : 100 },
            3 : { "md" : 168, "content" : 176, "total" : 344 },
            4 : { "md" : 120, "content" : 124, "total" : 244 },
            5 : { "md" : 128, "content" : 132, "total" : 260 }
        }

        # read in the csv and check it contains the right values
        seen = []
        with open(REPORT_FILE, "r") as f:
            reader = csv.reader(f)
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                seen.append(row[0])
                if row[0] not in ["Total", "Unique"]:
                    cfg = notes_final.get(row[0])
                    for mon, dist in cfg.items():
                        mdcol = 3*mon - 1
                        ctcol = mdcol + 1
                        totcol = mdcol + 2
                        assert int(row[mdcol]) == dist.get("md"), "found " + row[mdcol] + ", expected " + str(dist.get("md")) + " for " + row[0] + " col " + str(mdcol)
                        assert int(row[ctcol]) == dist.get("content")
                        assert int(row[totcol]) == dist.get("total")
                elif row[0] == "Total":
                    for mon, dist in grand_totals.items():
                        mdcol = 3*mon - 1
                        ctcol = mdcol + 1
                        totcol = mdcol + 2
                        assert int(row[mdcol]) == dist.get("md"), "found " + row[mdcol] + ", expected " + str(dist.get("md")) + " for " + row[0] + " col " + str(mdcol)
                        assert int(row[ctcol]) == dist.get("content")
                        assert int(row[totcol]) == dist.get("total")
                elif row[0] == "Unique":
                    for mon, dist in unique_totals.items():
                        mdcol = 3*mon - 1
                        ctcol = mdcol + 1
                        totcol = mdcol + 2
                        assert int(row[mdcol]) == dist.get("md"), "found " + row[mdcol] + ", expected " + str(dist.get("md")) + " for " + row[0] + " col " + str(mdcol)
                        assert int(row[ctcol]) == dist.get("content")
                        assert int(row[totcol]) == dist.get("total")

        # just check the coverage
        for k in list(notes_final.keys()):
            assert k in seen

        assert "Total" in seen
        assert "Unique" in seen

    def test_04_scheduling(self):
        now = datetime.now()
        scheduler.monthly_reporting()
        assert os.path.exists(os.path.join(RESOURCES, "monthly_notifications_to_institutions_" + str(now.year) + ".csv"))
