import os
from flask import Flask


app = Flask(__name__, template_folder="../Src/templates/", static_folder="../Src/static/")

import App.Views.main
import App.Views.band_gen