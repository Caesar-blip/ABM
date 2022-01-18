import csv 

income_brackets  = []
people_in_bracket = []

with open('./source_data/incomedistr.csv') as file:
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


with open('incomes.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for i in range(len(people_in_bracket)):
        writer.writerow([income_brackets[i][0], income_brackets[i][1], people_in_bracket[i]])
f.close()

######################## old ##############################
# incomes  = []
# counts = []

# with open('incomes.csv') as file:
#     csv_reader = csv.reader(file, delimiter=',')
#     for row in csv_reader:
#         incomes.append([int(row[0]),int(row[1])])
#         counts.append(int(row[2]))

# print(len(incomes))
# print(len(counts))

# cum_counts = []
# for i in range(len(counts)):
#     cum_counts.append(sum(counts[:i+1]))

# hhld_count = sum(counts)
# print(hhld_count)

# ratios = [x / hhld_count for x in counts]
# cum_ratios = [x / hhld_count for x in cum_counts]

# print(cum_ratios)
# print(len(cum_ratios))

# random.random()

# for i in range(len(incomes)):
#     if random.random() < cum_ratios[i]:
#         self.income = random.randint(incomes[i][0], incomes[i][1])


