#! /bin/bash

python3 -m venv .venv
. .venv/bin/activate

pip install -r ../TizEx/requirements.txt
npm install

mkdir -p node_js_codes

for item in $(ls ../benchmarks); do
    if [[ $item =~ 1[3,4,5]$ ]]; then
        # web13 and web14 and web15 need to be shuffled twice
        python3 ../TizEx/TizEx.py --html ../benchmarks/$item/index.html --baseUri ../benchmarks/$item --shuffle 2
    else
        python3 ../TizEx/TizEx.py --html ../benchmarks/$item/index.html --baseUri ../benchmarks/$item
    fi
    mv Tizex_analyze.js node_js_codes/Tizex_analyze${item:3}.js

    echo 'starting '$item'...'
    time ../expoSE node_js_codes/Tizex_analyze${item:3}.js
    echo 'finished!'
done



