## TizEx

TizEx is a tool which is used alongside [ExpoSE](https://github.com/ExpoSEJS/ExpoSE), in order to automatically find XSS and HTMLi vulnerabilities in web applications, especially [Tizen](https://www.tizen.org/) application. Tizen is an open-source operating system used in IoT devices. ExpoSE is an application which symbolically executes NodeJS applications.

Web applications can not be analyzed by ExpoSE directly. Because, as it has been said, ExpoSE analyzes NodeJS applications. Web applications are not just some scripts. Even JS scripts used in a web application can't be analyzed using ExpoSE. There are some reasons for that. As an example, they use some data structures such as `document` which are undefined in NodeJS. Also, in order to use ExpoSE to analyze NodeJS codes, symbolic variables should be specified explicitly.
TizEx does some preprocessing on web application, extracts its JS scripts, extracts its events, and defines data structures in a way that suits the needs for ExpoSE analyzing. Finally, it creates a file which can be used by ExpoSE to analyze if the web application is vulnerable or not.

### Installation

In order to run the application, first ExpoSE should be installed. In order to do that, [ExpoSE docs](https://github.com/ExpoSEJS/ExpoSE) can be used.

After installing ExpoSE, install TizEx requirements. To do that run the following command while being in the `/Web` directory:
```
pip install -r TizEx/requirements.txt
```

### Usage

In order to run the program, either HTML or JS file paths should be specified. There are some differences between them. if HTML path is been passed, the program will consider all of the scripts in the specified HTML file. Also bundled events in HTML using some attributes such as `onchange` will be considered. On the other hand, if js path is passed, only the specified JS file will be analyzed.
Also, if HTML path has been specifed, base URI should be specified, too. It is because of relative paths in HTML files for JS scripts.
Also, there are two optional parameters. In order to simulate, events on HTML pages, the program shuffles event callback functions and runs them. By default, it will happen only once. It is possible to shuffle functions more than once. Also, it is possible to specify some scripts in HTML file as CDNs, to not to analyze. In order to do that, one can pass script tag number in the order given in HTML code.

```
--html path/to/html/file   :  HTML file path
--js path/to/js/file       :  JS file path
--baseUri                  :  Base URI path
--cdns                     :  CDNs in HTML file
--shuffle                  :  Number of shufflings of callback function events
```

After creating the output file, one can use ExpoSE to find if it is vulnerable to XSS and HTMLi.


### Example

There is a web application in `Tizen` dirctory, which is based on a sample of tizen studio web application. It is vulnerable to XSS and HTMLi. In order to analyze it the following command should be run:
```
python3 TizEx/TizEx.py --html Tizen/index.html --baseUri ~/TizEx/Tizen/ 
```
A new file named `Tizex_analyze.js` will be created. This file can be analyzed by ExpoSE. In order to start expose run:
```
./expose ui
```
![ExpoSE ScreenShot](/Web/ExpoSE_results.png)


Alternatively, it is possibel to run expose in terminal:
```
./expose Tizex_analyze.js
```
