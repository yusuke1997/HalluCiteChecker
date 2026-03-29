<h1 align="center">
HalluCiteChecker
</h1>

<p align="center">
<a href="https://pypi.org/project/HalluCiteChecker"><img alt="PyPi" src="https://img.shields.io/pypi/v/hallucitechecker"></a>
<a href="https://github.com/yusuke1997/HalluCiteChecker/blob/main/LICENSE"><img alt="GitHub" src="https://img.shields.io/github/license/yusuke1997/HalluCiteChecker.svg"></a>
<a href="https://pypi.org/project/HalluCiteChecker">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</a>
<p align="center">

<p align="center">
<img src="https://raw.githubusercontent.com/yusuke1997/HalluCiteChecker/main/assets/overview.png" height="480px">
</p>

>  [!NOTE]
>
> Due to a NumPy-related issue, installation with Python 3.10 was not supported. We support Python 3.11 and later versions. Users who attempted to install the package with Python 3.10 may have encountered installation errors. Please try again using Python 3.11 or a later version.

>  [!NOTE]
>
>　We've prepared a demonstration on **Google Colab**. Please give it a try!!
> https://colab.research.google.com/drive/1MuMCc__yuAMjZM8WCGa5sSel6werwNFX?usp=sharing



## Installation

You can install from PyPi:

``` bash
pip install hallucitechecker
```

For developers, it can be installed from the source.

``` bash
git clone git@github.com:yusuke1997/HalluCiteChecker.git
cd HalluCiteChecker/
pip install ./
```

For uv users:
``` bash
uv add hallucitechecker
```

## Quick start

``` bash
hallucitechecker -i manuscript.pdf
```
If it is detected, it will be displayed in the CLI.

You can treat multiple PDF files at once.

``` bash
hallucitechecker -i manuscript1.pdf manusctipt2.pdf
or
hallucitechecker -i manuscripts_dir/*
```

If you get a PDF with highlights, please specify the output directory.
``` bash
hallucitechecker -i manuscript.pdf -o results_dir
```

If a hallucitation is detected, a PDF will be generated. If everything is clear, no PDF will be generated. In other words, you only need to manually verify the PDFs in the output directory.

We prepared the demonstration on Google Colab.

https://colab.research.google.com/drive/1MuMCc__yuAMjZM8WCGa5sSel6werwNFX?usp=sharing
