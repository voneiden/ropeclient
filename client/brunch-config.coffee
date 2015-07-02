exports.config =
  # See http://brunch.readthedocs.org/en/latest/config.html for documentation.
  plugins:
    stylus:
      paths: [
        './app/assets/images',
      ]

  files:
    javascripts:
      joinTo:
        'js/rc.js': /^app/
        'js/vendor.js': /^bower_components/
      order:
        before: []

    stylesheets:
      joinTo:
        'css/rc.css': /^(app|bower_components)/
      order:
        before: []
        after: []

    # Ensure that our jade templates don't get compiled into our app JS.
    templates:
      joinTo: 'javascripts/template.js'
  modules:
    nameCleaner: (path) ->
      path = path.replace(/^app\//, '')
      path = path.replace(/^javascripts\//, '')


  #plugins:
  #  jaded:
  #    staticPatterns: /^app(\/|\\)static(\/|\\)(.+)\.jade$/
