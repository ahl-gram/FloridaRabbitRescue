import os
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, os.pardir, "scripts"))

import verify_sunbiz as vs  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")


def make_record(doc, name, status="A", reports=()):
    """A synthetic 1442-byte cordata record. `reports` is up to three (year, MMDDYYYY) pairs."""
    rec = [" "] * vs.CORDATA_PAYLOAD

    def put(start, value):
        rec[start:start + len(value)] = list(value)

    put(0, doc)
    put(12, name)
    put(204, status)
    put(205, vs.NONPROFIT_FILING_TYPE)
    for (year, date), (y_start, _), (d_start, _) in zip(reports, vs.REPORT_YEARS, vs.REPORT_DATES):
        put(y_start, year)
        put(d_start, date)
    return "".join(rec) + "\r\n"


FIXTURE_RECORDS = [
    make_record("N99000000001", "FIRST TEST RABBIT RESCUE INC", reports=[("2026", "04302026")]),
    make_record("N99000000002", "SECOND TEST BUNNY RESCUE INC", status="I"),
    make_record("N99000000003", "THIRD TEST RABBIT SANCTUARY INC"),
]


class IterRecordsTest(unittest.TestCase):
    def test_reads_deflate_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cordata.zip")
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("cordata0.txt", "".join(FIXTURE_RECORDS))
            docs = [r[:12] for r in vs.iter_records(path, vs.CORDATA_RECORD, vs.CORDATA_PAYLOAD)]
        self.assertEqual(docs, ["N99000000001", "N99000000002", "N99000000003"])

    def test_reads_deflate64_archive(self):
        path = os.path.join(FIXTURES, "cordata-deflate64.zip")
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(archive.infolist()[0].compress_type, 9, "fixture must be Deflate64")
        records = list(vs.iter_records(path, vs.CORDATA_RECORD, vs.CORDATA_PAYLOAD))
        self.assertEqual([r[:12] for r in records],
                         ["N99000000001", "N99000000002", "N99000000003"])
        self.assertEqual(records[0], FIXTURE_RECORDS[0][:vs.CORDATA_PAYLOAD])


class LatestAnnualReportTest(unittest.TestCase):
    def test_picks_newest_year_then_newest_date(self):
        record = make_record("N99000000001", "X", reports=[
            ("2026", "01052026"), ("2026", "04302026"), ("2025", "12312025")])
        self.assertEqual(vs.latest_annual_report(record), ("2026", "04/30/2026"))

    def test_ignores_empty_slots(self):
        record = make_record("N99000000001", "X", reports=[("2025", "03062025")])
        self.assertEqual(vs.latest_annual_report(record), ("2025", "03/06/2025"))

    def test_none_when_no_report_filed(self):
        self.assertIsNone(vs.latest_annual_report(make_record("N99000000001", "X")))


if __name__ == "__main__":
    unittest.main()
