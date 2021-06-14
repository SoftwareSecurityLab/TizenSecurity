from shared import *
import subprocess

def init(fin, fout):
    # fin is the file handler of input stream
    # fout is the file handler of output stram

    # writing initial objects to f 
    if not isinstance(fin, io.IOBase) or not isinstance(fout, io.IOBase):
        raise ValueError('f must be a file!')

    initial_code = '''
    var S$ = require('S$');\n
    class element {
        constructor(name) {
            this.name = name;
            this.innerHTML = new S$.symbol(name + 'html', '');
            this.innerText = new S$.symbol(name + 'text', '');
        }
        addEventListener(event, f) {
            f(S$.symbol(this.name + event, {}));
        }
    }

    document = {
        getElementById: function (name) {
            return new element(name);
        }
    }\n 
    class Promise {
        static increaseCount() {
            this.count++;
        }

        constructor(callBack, init='') {
            Promise.increaseCount();
            this.status = Array();
            function resolved(a) {
                this.status.push('fullfilled');
                this.resolved_return = a;
            }

            function rejected(a) {
                this.status.push('rejected');
                this.rejected_return = a;
            }
            this.resolved_bind = resolved.bind(this);
            this.rejected_bind = rejected.bind(this);
            this.result = S$.symbol('Promise' + Promise.count, init);
            callBack(this.resolved_bind, this.rejected_bind);
            this.final_status = this.status[0];
        }

        then(onSuccess, onFailure=undefined){
            if (this.final_status == 'fullfilled') {
                onSuccess(this.result);
            } else {
                onFailure(this.result);   // there will be an error if onFailure is not defined!
            }
            return this;
        }

    };
    Promise.count = 0;

    function fetch(type, url) {
        if (!isEquivalent({}, type) && !isEquivalent('', type) && !isEquivalent(type, []) && !typeof type === 'number' && !typeof type === 'boolean' && !typeof type == 'undefined') {
            type = {};
        }
        return new Promise(function(res, rej) {
            res('abc');
            rej('def');
        }, type)
    }

    function isEquivalent(a, b) {
        // Create arrays of property names
        var aProps = Object.getOwnPropertyNames(a);
        var bProps = Object.getOwnPropertyNames(b);

        // If number of properties is different,
        // objects are not equivalent
        if (aProps.length != bProps.length) {
            return false;
        }

        for (var i = 0; i < aProps.length; i++) {
            var propName = aProps[i];

            // If values of same property are not equal,
            // objects are not equivalent
            if (a[propName] !== b[propName]) {
                return false;
            }
        }

        // If we made it this far, objects
        // are considered equivalent
        return true;
    }
    '''
    
    # beautifying code
    subprocess.run(f'html5-print -t js -o tmp {fin.name}'.split())

    print(initial_code, file=fout)