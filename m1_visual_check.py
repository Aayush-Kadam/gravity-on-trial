"""Small contact sheet for visual QA of eight scientific figures."""
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent/'results/m1/v1'
files=sorted(root.glob('*_comparison.png'))
sheet=Image.new('RGB',(1000,440*((len(files)+1)//2)),'white');draw=ImageDraw.Draw(sheet)
for i,p in enumerate(files):
    with Image.open(p) as im:
        im.thumbnail((500,415));sheet.paste(im,(500*(i%2),440*(i//2)+20))
    draw.text((500*(i%2)+5,440*(i//2)+3),p.stem,fill='black')
sheet.save(root/'figure_contact_sheet.png')
