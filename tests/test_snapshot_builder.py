from __future__ import annotations

import importlib.util
import sys
from datetime import timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "custom_components" / "mojv"
MODULE = PACKAGE / "snapshot_builder.py"


def _load():
    assert MODULE.exists(), "snapshot_builder.py must unify live payload parsing"

    package_name = "mojv_snapshot_builder_test_pkg"
    package_spec = importlib.util.spec_from_file_location(
        package_name,
        PACKAGE / "__init__.py",
        submodule_search_locations=[str(PACKAGE)],
    )
    assert package_spec is not None
    package = importlib.util.module_from_spec(package_spec)
    sys.modules[package_name] = package

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.snapshot_builder",
        MODULE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_builder_combines_plan_attendance_grades_and_schoolwork() -> None:
    builder = _load()
    snapshot = builder.build_student_snapshot(
        student_id="1",
        name="Jan",
        class_name="5A",
        timetable=[
            {
                "data": "2026-09-03",
                "godzinaOd": "08:00",
                "godzinaDo": "08:45",
                "przedmiot": "Matematyka",
                "sala": "12",
            }
        ],
        attendance=[
            {
                "data": "2026-09-03",
                "godzinaOd": "08:00",
                "kategoriaFrekwencji": 1,
            }
        ],
        classification_periods=[{"id": 101, "numerOkresu": 1}],
        grades_by_period={
            "101": {
                "ocenyPrzedmioty": [
                    {
                        "przedmiotNazwa": "Matematyka",
                        "proponowanaOcenaOkresowa": "5",
                        "ocenaOkresowa": "4",
                        "kolumnyOcenyCzastkowe": [
                            {
                                "idKolumny": 7,
                                "kategoriaKolumny": "Sprawdzian",
                                "nazwaKolumny": "Ułamki",
                                "oceny": [
                                    {"wpis": "5", "dataOceny": "03.09.2026"}
                                ],
                            }
                        ],
                    }
                ]
            }
        },
        schoolwork=[
            {
                "id": 8,
                "typ": 4,
                "data": "2026-09-05",
                "przedmiotNazwa": "Matematyka",
                "temat": "Zadanie 4",
            }
        ],
        timezone=timezone.utc,
    )

    assert snapshot.student.name == "Jan"
    assert len(snapshot.lessons) == 1
    assert snapshot.lessons[0].attendance == "present"
    assert snapshot.lessons[0].start.tzinfo == timezone.utc
    assert len(snapshot.grades) == 1
    assert snapshot.grades[0].value == "5"
    assert snapshot.grades[0].date.tzinfo == timezone.utc
    assert len(snapshot.final_grades) == 1
    assert snapshot.final_grades[0].proposed == "5"
    assert len(snapshot.schoolwork) == 1
    assert snapshot.schoolwork[0].kind == "homework"
    assert snapshot.schoolwork[0].date.tzinfo == timezone.utc
