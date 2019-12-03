"""Dispatch anything to anything.

Well... for now, a list of functions to cli, ws, or dash.

"""


def dispatch_funcs(funcs, interface=None, *args, **kwargs):
    if interface is None:
        print("Choices of interface:")
        print(", ".format(['cli', 'ws', 'dash']))
        return

    if not isinstance(funcs, (tuple, list)):
        funcs = [funcs]

    if interface == 'cli':
        print('Hi!')
        from argh import dispatch_commands

        return dispatch_commands(funcs)

    elif interface == 'ws':
        from py2api.py2rest.app_maker import dflt_run_app_kwargs, dispatch_funcs_to_web_app

        app = dispatch_funcs_to_web_app(funcs, *args, **kwargs)

        run_app_kwargs = kwargs.get('run_app_kwargs', dflt_run_app_kwargs)
        app.run(**run_app_kwargs())

    elif interface == 'dash':

        from py2dash.app_makers import dispatch_funcs

        app = dispatch_funcs(funcs)
        debug = kwargs.get('debug', False)
        app.run_server(debug=debug)
