import json, os
fpath = os.path.join(os.path.dirname(__file__), 'instance', 'offline_scoreboard_data.json')
with open(fpath, 'r', encoding='utf-8') as f: data = json.load(f)

sid=60; month='2026-03'

scores = [r for r in data.get('scores', []) if int(r.get('studentId',0))==sid and (str(r.get('month','')).strip()==month or str(r.get('date','')[:7])==month)]
points_total=sum(int(r.get('points',0)) for r in scores)
star_total=sum(max(0,int(r.get('stars',0))) for r in scores)
adv=0
for d in data.get('resource_advantage_deductions',[]):
    if int(d.get('studentId',0))==sid and str(d.get('month','')).strip()==month and not d.get('reversed'):
        adv += int(d.get('points_deducted',0))
print('points:', points_total, 'stars>', star_total,'advdeduct',adv, 'calc', points_total+star_total*100-adv)

for m in ['2025-06','2026-03']:
    scores=[r for r in data.get('scores', []) if int(r.get('studentId',0))==sid and (str(r.get('month','')).strip()==m or str(r.get('date','')[:7])==m)]
    points=sum(int(r.get('points',0)) for r in scores)
    stars=sum(max(0,int(r.get('stars',0))) for r in scores)
    # getStudentMonthTotal (points+penalty) from getStudentMonthTotal, we'll ignore penalty for now
    print('month',m, 'points',points,'stars',stars,'stars+100',points+stars*100)
