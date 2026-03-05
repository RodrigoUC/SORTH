import camelot
import json

pdfs = [
    "BACHILLERATO EN BIOLOGÍA CON ÉNFASIS EN BIOLOGIA MARINA.pdf",
    "BACHILLERATO EN BIOLOGÍA CON ÉNFASIS EN BIOLOGÍA TROPICAL BA-BIOLOG 2021-10.pdf",
    "BACHILLERATO EN BIOTECNOLOGIA.pdf"
]

courses = {}

for pdf in pdfs:

    tables = camelot.read_pdf(pdf, pages="all", flavor="stream")

    for table in tables:

        df = table.df

        for _, row in df.iterrows():

            code = row[2].strip() if len(row) > 2 else ""
            name = row[3].strip() if len(row) > 3 else ""

            if not code or not code[:3].isalpha():
                continue

            try:
                t = int(row[6])
                p = int(row[7])
                l = int(row[8])
                duration = max(t, p, l)
            except:
                continue

            courses[code] = {
                "code": code,
                "name": name,
                "number_of_groups": 0,
                "duration": duration,
                "suggested_classroom": None
            }

data = {"courses": list(courses.values())}

with open("courses.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("JSON generado correctamente")