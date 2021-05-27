import argparse

parser = argparse.ArgumentParser()

parser.add_argument('versionfile', help='the file containing the version', type=str)
parser.add_argument(
    '--importance', 
    help='whether te update is major minor or a hotfix', 
    type=str, 
    choices={'major', 'minor', 'hotfix'},
    default='hotfix'
)
parser.set_defaults(quick=False)

args = parser.parse_args()

with open(args.versionfile, 'r') as r:
    version_str = r.read()

major, minor, hotfix =  tuple([int(v) for v in version_str.split('.')])

if args.importance == 'major':
    major += 1
    minor = 0
    hotfix = 0
elif args.importance == 'minor':
    minor += 1
    hotfix = 0
else:
    hotfix += 1

with open(args.versionfile, 'w') as r:
    r.write(f'{major}.{minor}.{hotfix}')

