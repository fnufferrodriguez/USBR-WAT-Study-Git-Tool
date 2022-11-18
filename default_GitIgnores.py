'''
Created on 11/18/2022
@author: scott
@organization: Resource Management Associates
@contact: scott@rmanet.com
@note:
'''
import os

def getDefaultGitIgnore(name, filepath):
    makegitignore = False
    if name.lower() == 'main':
        gitfilepath = os.path.join(filepath, '.gitignore')
        if not os.path.exists(gitfilepath):
            makegitignore = True
            contents = ["runs/",
                        "layouts/",
                        "**/*.bak",
                        "**/*.bak.*",
                        "**/*.log",
                        "**/*.wqEngineLog",
                        "**/*.h5",
                        "hms/*.out",
                        "*.access",
                        "*.sty.access",
                        "*/.access"
                        ]


    elif name.lower() == 'cequal-w2':
        gitfilepath = os.path.join(filepath, '.gitignore')
        if not os.path.exists(gitfilepath):
            makegitignore = True
            contents = ["**/*.opt",
                        "!**/pre.opt",
                        "!**/PREW2CodeCompilerVersion.opt",
                        "**/*.exe",
                        "**/*.bak",
                        "**/*.bak.*",
                        "**/*.log"
                        ]

    elif name.lower() == 'rss':
        gitfilepath = os.path.join(filepath, '.gitignore')
        if not os.path.exists(gitfilepath):
            makegitignore = True
            contents = ["**/*.bak",
                        "**/*.bak.*",
                        "**/*.log",
                        "**/*.wqEngineLog",
                        "**/*.h5",
                        "**/simulation.dss"
                        ]

    elif name.lower() == 'reports':
        gitfilepath = os.path.join(filepath, '.gitignore')
        if not os.path.exists(gitfilepath):
            makegitignore = True
            contents = ["*.xml",
                        "!defaultLineStyles.xml",
                        "!Graphics_Defaults.xml",
                        "!Graphics_Defaults_contour.xml",
                        "!Format/*.xml",
                        "!Datasources/USBRAutomatedReportDataAdapter.xml",
                        "**/*.bak",
                        "**/*.bak.*",
                        "**/*.log",
                        "*.jasper",
                        "Images/**",
                        "CSVData/**",
                        "Datasources/USBRAutomatedReportOutput.xml",
                        "jasperC/**",
                        "jasperC/",
                        "jasperC/*.jasper"
                        ]

    else: #default
        gitfilepath = os.path.join(filepath, '.gitignore')
        if not os.path.exists(gitfilepath):
            makegitignore = True
            contents = ["*.log",
                        "*.bak",
                        "**/*.log",
                        '**/*.bak'
                        ]

    if makegitignore:
        with open(gitfilepath, 'w') as gfp:
            for item in contents:
                gfp.write(f'{item}\n')
