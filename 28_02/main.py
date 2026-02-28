logs = [
    "2025-02-01 10:15:33|INFO|user=anna action=login status=success ip=10.0.0.1",
    "2025-02-01 10:17:10|ERROR|user=bob action=payment status=fail amount=120",
    "2025-02-01 10:20:01|INFO|user=anna action=logout status=success",
    "2025-02-01 10:22:45|WARNING|user=anna action=payment status=fail amount=300",
    "2025-02-01 10:30:12|ERROR|user=tom action=login status=fail ip=10.0.0.5"
]

parsed_logs = []

for line in logs:
    parts = line.split("|")

    date = parts[0]
    level = parts[1]
    message = parts[2]

    fields = message.split(" ")
    data = {}

    for f in fields:
        kv = f.split("=")
        data[kv[0]] = kv[1]

    data["date"] = date
    data["level"] = level

    parsed_logs.append(data)


print("---- FAIL ONLY ----")
for log in parsed_logs:
    if log["status"] == "fail":
        print(log)

print("---- ONLY ERRORS ----")
for log in parsed_logs:
    if log["level"] == "ERROR":
        print(log)

print("---- ONLY anna ----")
for log in parsed_logs:
    if log.get("user") == "anna":
        print(log)


print("---- COUNT BY LEVEL ----")
info = 0
error = 0
warning = 0

for log in parsed_logs:
    if log["level"] == "INFO":
        info += 1
    if log["level"] == "ERROR":
        error += 1
    if log["level"] == "WARNING":
        warning += 1

print(info, error, warning)