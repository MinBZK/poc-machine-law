def before_scenario(context, scenario):
    context.test_data = {}
    context.service_context = {}
    context.result = None


def after_scenario(context, scenario):
    pass
