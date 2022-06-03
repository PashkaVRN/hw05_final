from datetime import datetime


def year(request):
    dt = datetime.now().year
    return {'year': dt}
