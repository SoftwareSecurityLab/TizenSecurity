def add_events(fout, times):
    # adds some loops at the end of the code to run events
    js = '''
    window.onload();
    function shuffle(array) {
        var currentIndex = array.length,  randomIndex;

        while (0 !== currentIndex) {

        randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex--;

        [array[currentIndex], array[randomIndex]] = [
            array[randomIndex], array[currentIndex]];
        }

        return array;
    }
    '''
    print(js, file=fout)
    for i in range(times):
        js = '''
        shuffle(TizEx_events_js);
        shuffle(TizEx_events_html);
        for (let i = 0; i < TizEx_events_js.length; i++) {
            let f = TizEx_events_js[i][0];
            let symbolic = TizEx_events_js[i][1];
            f(symbolic);
        }
        '''
        print(js, file=fout)