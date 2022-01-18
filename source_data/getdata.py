import csv 

income_brackets  = []
people_in_bracket = []

with open('CBS_incomedistr.csv') as file:
    csv_reader = csv.reader(file, delimiter=';')
    next(csv_reader)
    next(csv_reader)
    next(csv_reader)
    next(csv_reader)
    for row in csv_reader:
        income_bracket = [int(s) for s in row[0].split() if s.isdigit()]
        people = row[1]

        income_brackets.append(income_bracket)
        people_in_bracket.append(people)
file.close()


with open('../input_data/incomes.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for i in range(len(people_in_bracket)):
        writer.writerow([income_brackets[i][0], income_brackets[i][1], people_in_bracket[i]])
f.close()


total_pop_count = []
ages = []
age_counts = []

with open('CBS_agedistr.csv') as file:
    csv_reader = csv.reader(file, delimiter=';')
    for i in range(8):
        next(csv_reader)
    count = 0
    for row in csv_reader:
        # check for weird data point and exclude it
        if row[0] == "95 jaar of ouder":
            continue

        if count == 0:
            total_pop_count = row[1]
            count += 1
            continue
        
        for s in row[0].split():
            if s.isdigit():
                ages.append(int(s))
                
        age_counts.append(int(row[1]))
file.close()

# remove age groups above 100
del ages[-5:]
del age_counts[-5:]

with open('../input_data/ages.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for i in range(len(ages)):
        writer.writerow([ages[i], age_counts[i]])
f.close()


