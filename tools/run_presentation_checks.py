"""Run an existing presentation suite with screenshots outside tracked brand assets.
Example: python3 tools/run_presentation_checks.py camera --artifacts docs/phase-c/existing-checks
Assertions, fixtures and command failure status are preserved.
"""
import argparse,runpy,sys
from pathlib import Path
from playwright.async_api import Page,Locator
parser=argparse.ArgumentParser()
parser.add_argument('suite',choices=['camera','tabletop','inspection','cards','sprite_art'])
parser.add_argument('--artifacts',type=Path,default=Path('/tmp/darb-presentation-checks'))
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
def redirect(original):
 async def screenshot(self,*positional,**kwargs):
  if kwargs.get('path'):kwargs['path']=str(args.artifacts/Path(kwargs['path']).name)
  return await original(self,*positional,**kwargs)
 return screenshot
for kind in [Page,Locator]:kind.screenshot=redirect(kind.screenshot)
sys.path.insert(0,str(Path(__file__).resolve().parent))
runpy.run_path(str(Path(__file__).with_name(f'verify_{args.suite}.py')),run_name='__main__')
