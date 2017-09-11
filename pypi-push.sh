#! /bin/bash

printf "   loading module Python 3.6\n"
ml Python > /dev/null 2>&1

version=$(grep ^__version__ setup.py | cut -d'"' -f2)

pandoc --columns=100 --output=README.rst --to rst README.md
git add README.rst
git commit -a -m "version ${version}"
git tag ${version} -m "tag for PyPI"
git push --tags origin master
python3 setup.py register -r pypi
python3 setup.py sdist upload -r pypi

echo "  Done! Occasionally you may want to remove older tags:"
echo "git tag 1.2.3 -d"
echo "git push origin :refs/tags/1.2.3"
