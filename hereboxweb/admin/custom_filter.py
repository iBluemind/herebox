from hereboxweb import app


@app.template_filter('translate_time')
def visit_time_filter(s):
    if s == 1:
        return "10:00-12:00"
    elif s == 2:
        return "12:00-14:00"
    elif s == 3:
        return "14:00-16:00"
    elif s == 4:
        return "16:00-18:00"
    elif s == 5:
        return "18:00-20:00"
    elif s == 6:
        return "20:00-22:00"