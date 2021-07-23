def add_events(fout, times):
    # adds some loops at the end of the code to run events
    js = '''
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
        shuffle(TizEx_events);
        for (var i = 0; i < TizEx_events.length; i++) {
            var f = TizEx_events[i][0];
            var symbolic = TizEx_events[i][1];
            f(symbolic);
        }
        '''
        print(js, file=fout)