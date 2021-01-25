# Client JS

This module provides a mechanism to build and serve configuration for the client in javascript

Bind this module in your app, with

```python
    from octopus.modules.clientjs.configjs import blueprint as configjs
    app.register_blueprint(configjs)
```

This will then respond to any requests at the url

    /javascript/config.js

It will extend the base **octopus** javascript object with a **config** parameter, which in turn will contain all
configuration marked in your various settings.py files to be passed through to the UI.

In order to mark a setting for being passed through to the UI, in your settings.py file(s), use

```python
    CLIENTJS_YOUR_CONFIG_OPTION = "some value"
```

This will mean that a config variable with the name "your_config_option" will be available in **octopus.config** on the client
side, so you can access it with **octopus.config.your_config_option**.  Note that the CLIENTJS_ prefix is removed, and the 
option name is converted to lower case.