# nctoolreader.py
# V0.1 by Pete Oxenham
# Intended to take a Hass lathe program backup file (.PGM) and output a summary of each program to a CSV

import csv, sys

if len(sys.argv) != 3:
    print('Please define input and output file:')
    print('nctoolreader.py <inputfile> <outputfile>')
    sys.exit()
else:
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]

if not outputfile.endswith('.csv'):
    print('Output must be a .csv file')
    sys.exit()

print('Input:', inputfile)
print('Output:', outputfile)

# Length of program number format, default 6 (ex: O00001)
prgmNoLen = 6

# Columns we want to export to CSV
csvCol= ['name', 'number', 'toolstr', 'useBarfeed']

programs = []

# Open the File
with open (inputfile, 'r') as file:
    data=file.read().splitlines()

# Look for programs and get their names, initialize dict. Assumes format for program first line is: "O00001 (My Program)"
for i, line in enumerate(data):
    if len(line) > 0:
        if line[0] == 'O':
            number = line[:prgmNoLen]
            if '(' in line and ')' in line:
                name = line[line.find('(')+1:line.find(')')]
            else:
                name = None
            startln = i
            programs.append(
                {
                    'number':number,
                    'name':name,
                    'startln':startln,
                    'endln':None,
                    'contents':None,
                    'tools':[],
                    'toolstr':'',
                    'useBarfeed': False
                }
            )

# Second pass of programs, figure out where their end line is based on beginning line of next program.
# Add contents of each program
# Probably could do this all in one for loop, but I didn't

for i, program in enumerate(programs):
    if i < len(programs)-1:
        program['endln'] = programs[i+1]['startln']-1
        program['contents'] = data[program['startln']+1:program['endln']]
    else:
        program['endln'] = len(data)
        program['contents'] = data[program['startln']+1:len(data)]
    
    for i, line in enumerate(program['contents']):
        if len(line) > 0 and line[0] == 'T':
            if ' ' in line:
                traw = str(line).split()[0]
            else:
                traw = str(line)
            tool={}
            if len(traw) == 4:
                tool['no'] = traw[1]
                tool['offset'] = traw[3]
            if len(traw) == 5:
                tool['no'] = traw[1:3]
                tool['offset'] = traw[3:5]

            tool['startln'] = i
            tool['endln'] = None
            tool['type'] = ''
            
            program['tools'].append(tool)
    
    for i, tool in enumerate(program['tools']): 
        program['toolstr'] += tool['no'] + ', '
        if i+1 < len(program['tools']):
            tool['endln'] = program['tools'][i+1]['startln']-1
        else:
            tool['endln'] = len(program['contents'])-1

        toolprgm = program['contents'][tool['startln']:tool['endln']]

        # Try to figure out what kind of tool it is. Doesn't work that well right now, so we're not using this yet.
        if any('G84' in line for line in toolprgm):
            tool['type'] += 'Tap'
        if any('G71' in line for line in toolprgm):
            tool['type'] += 'Rough OD'
        if any('M133' or 'M134' in line for line in toolprgm):
            tool['type'] += 'Live Tool'

    if len(program['toolstr']) > 1 and program['toolstr'][-2] == ',':
        program['toolstr'] = program['toolstr'][:-2]
    
    # See if the program uses the barfeeder
    if 'G105' in program['contents']:
        program['useBarfeed'] = True

# Write out program summaries to command line
if False:
    for program in programs:
        print('Name:', program['number'])
        print('Number:', program['name'])
        if program['tools']:
            print('Tools:')
            for tool in program['tools']:
                print('\tTool', tool['no'])
        else:
            print('No tools in program')
        if program['useBarfeed']:
            print('Uses Bar Feeder')
        print('----------------------')

# Export to CSV
try:
    with open(outputfile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csvCol, extrasaction='ignore')
        writer.writeheader()
        for program in programs:
            writer.writerow(program)
except IOError:
    print("I/O error")

print('Success!')