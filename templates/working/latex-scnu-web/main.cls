% 定义包名
\ProvidesClass{main}
\LoadClass[a4paper]{article}
\RequirePackage[heading]{ctex} % Required for the Chinese and the corresponding section setting
\RequirePackage[includeheadfoot]{geometry} % Required for the Word-like page
\geometry{top=1.5cm,bottom=1.75cm,left=30mm,right=30mm} % 上下左右的留白
\RequirePackage{fancyhdr} % Required for custom headers
\RequirePackage{setspace} % Required for the space setting
\RequirePackage{titlesec} % Required for the Chapter & Section fonts adjustment
\RequirePackage{titletoc} % Required for the Content fonts adjustment
\RequirePackage{float} % Required for the Here float
\RequirePackage{graphicx} % Required to insert images
\RequirePackage{booktabs} % Required for the hline of the three lines table
\RequirePackage{indentfirst} % Required for the indent before each paragraph
\RequirePackage{fontspec}
\setmainfont{Times New Roman}
\RequirePackage{hyperref}
\RequirePackage{url}
\RequirePackage[usenames,dvipsnames]{color} % Required for custom colors
\RequirePackage[font=footnotesize,tableposition=top]{caption} % Required for the footnote size captions of figures and tables
\RequirePackage{xcolor}
% 正文前的空白页
% 使用 \afterpage{\blankpage} 正文中的空白页 \afterpage{\null\newpage}
\RequirePackage{afterpage}
\newcommand\blankpage{
  \null
  \thispagestyle{empty}
  \addtocounter{page}{-1}
  \newpage
}
\RequirePackage{ifthen} % Required for the conditional commands
\newcommand{\ud}{\mathrm{d}} 
\makeatletter
\@addtoreset{equation}{section}
\makeatother

\renewcommand{\theequation}{\arabic{section}.\arabic{equation}}

\ctexset { section = { name={第,章},number={\chinese {section}},format={\centering \zihao {-2}\bfseries } } }
\titleformat{\subsection}{\zihao{-3}\bfseries}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\zihao{4}\bfseries}{\thesubsubsection}{1em}{}
\ctexset { paragraph = { ,format={\raggedright \bfseries \zihao {-4}} } }

\renewcommand\contentsname{目\quad\quad 录} % Setup contents
\titlecontents{section}[0em]{\zihao{4}\bfseries}{\contentspush{\thecontentslabel \hspace{0.7em}}}
              {}{\titlerule*[5pt]{.}\contentspage}
\titlecontents{subsection}[2.2em]{\zihao{-4}\songti}{\contentspush{\thecontentslabel\hspace{0.7em}}}
              {}{\titlerule*[5pt]{.}\contentspage}
\titlecontents{subsubsection}[3.9em]{\zihao{-4}\songti}{\contentspush{\thecontentslabel\hspace{0.7em}}}
              {}{\titlerule*[5pt]{.}\contentspage}
\titlespacing*{\subsection} {0pt}{1ex}{1ex} % Adjust the space between title and context
\titlespacing*{\subsubsection} {0pt}{1ex}{1ex}

% 页头页尾设置
\newcommand{\thesistitlefancyhead}{论文题目设置为页眉} % 定义论文题目为页眉
\pagestyle{fancy}
\fancyhf{}
\fancyhead{}
\fancyhead[C]{\thesistitlefancyhead{}} % 页眉设置为论文标题
\fancyfoot[C]{\thepage}
