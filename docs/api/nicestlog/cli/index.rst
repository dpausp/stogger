nicestlog.cli
=============

.. py:module:: nicestlog.cli

.. autoapi-nested-parse::

   Command-line interface for nicestlog.

   This module provides the complete CLI interface including both basic and advanced
   AST functionality, previously split between cli.py and cli_advanced.py.



Attributes
----------

.. autoapisummary::

   nicestlog.cli.run_dashboard
   nicestlog.cli.NicestLogConfig
   nicestlog.cli.logger
   nicestlog.cli.log
   nicestlog.cli.console
   nicestlog.cli.app
   nicestlog.cli.tools_app
   nicestlog.cli.FLASK_AVAILABLE_FOR_CLI
   nicestlog.cli.i18n_app
   nicestlog.cli.MIGRATION_TYPES


Classes
-------

.. autoapisummary::

   nicestlog.cli.MigrationResultProtocol
   nicestlog.cli.CheckOptions
   nicestlog.cli.MigrateOptions


Functions
---------

.. autoapisummary::

   nicestlog.cli.version_callback
   nicestlog.cli.main_callback
   nicestlog.cli.tools_generate_service
   nicestlog.cli.tools_check_advanced
   nicestlog.cli.tools_review
   nicestlog.cli.tools_journal
   nicestlog.cli.tools_dashboard
   nicestlog.cli.i18n_check
   nicestlog.cli.init_config
   nicestlog.cli.docs
   nicestlog.cli.docs_serve
   nicestlog.cli.init_config_cmd
   nicestlog.cli.check
   nicestlog.cli.migrate
   nicestlog.cli.tools_demo
   nicestlog.cli.run_dashboard_cmd
   nicestlog.cli.run_journal_viewer
   nicestlog.cli.run_log_reviewer
   nicestlog.cli.generate_service_cmd
   nicestlog.cli.run_demos
   nicestlog.cli.print_demo_header
   nicestlog.cli.run_basic_demo
   nicestlog.cli.run_i18n_demo
   nicestlog.cli.run_pii_demo
   nicestlog.cli.run_eliot_demo
   nicestlog.cli.run_systemd_demo
   nicestlog.cli.run_async_demo
   nicestlog.cli.run_complete_demo
   nicestlog.cli.run_lint_demo
   nicestlog.cli.run_migrate_command
   nicestlog.cli.migrate_single_file
   nicestlog.cli.migrate_directory_recursive
   nicestlog.cli.run_interactive_migration
   nicestlog.cli.migrate_directory_with_handler
   nicestlog.cli.show_migration_report
   nicestlog.cli.main


Module Contents
---------------

.. py:data:: run_dashboard
   :value: None


.. py:data:: NicestLogConfig
   :value: None


.. py:data:: logger

.. py:class:: MigrationResultProtocol

   Bases: :py:obj:`Protocol`


   Protocol for migration result types.


   .. py:attribute:: files_processed
      :type:  int


   .. py:attribute:: transformations_applied
      :type:  int


   .. py:attribute:: errors
      :type:  int


   .. py:attribute:: warnings
      :type:  list[str]


.. py:data:: log

.. py:data:: console

.. py:function:: version_callback(*, value)

   Show version and exit.


.. py:data:: app

.. py:function:: main_callback(version = None)

   Nicestlog utility.


.. py:data:: tools_app

.. py:function:: tools_generate_service(service_name = typer.Argument(..., help='Name of the service'), exec_command = typer.Argument(..., help='Command to execute'), user = typer.Option(None, '--user', help='User to run service as'), working_dir = typer.Option(None, '--working-dir', help='Working directory'), output = typer.Option(None, '--output', help='Output file path'))

   🔧 Generate systemd service file.


.. py:function:: tools_check_advanced(**kwargs)

   🔬 Advanced check with all options for complexity analysis and AST patterns.


.. py:function:: tools_review(path, format_type = 'text', min_score = 70.0)

   📝 Review log quality and provide suggestions.


.. py:function:: tools_journal(unit = None, lines = 50, *, follow = False, since = None, level = None)

   📖 Beautiful systemd journal viewer.


.. py:data:: FLASK_AVAILABLE_FOR_CLI

.. py:function:: tools_dashboard(host = '127.0.0.1', port = 8080, debug = False)

   🌐 Start the web dashboard.


.. py:data:: i18n_app

.. py:function:: i18n_check(src_dir = typer.Argument(..., help='Source directory to check'), translation_dir = typer.Option(None, '--translation-dir', help='Translation directory'), language = 'en', *, list_missing = False, fail_on_extra = False, strict = False, verbose = False)

   🌍 Check translation completeness and quality.


.. py:function:: init_config()

   Interactive wizard to create a [tool.nicestlog] section in pyproject.toml.


.. py:function:: docs(*, interactive = False, feature = None, pager = False)

   📚 Show documentation and examples.


.. py:function:: docs_serve(port = 8000, host = '127.0.0.1', *, open_browser = True, build = True)

   🌐 Serve HTML documentation in browser.


.. py:function:: init_config_cmd(path = typer.Argument('.', help='Project path to initialize'), template = typer.Option(None, '--template', help='Configuration template'), force = typer.Option(False, '--force', help='Overwrite existing config'))

   🔧 Initialize nicestlog configuration.


.. py:class:: CheckOptions

   Options for the check command.


   .. py:attribute:: path
      :type:  str
      :value: '.'



   .. py:attribute:: fix
      :type:  bool
      :value: False



   .. py:attribute:: interactive
      :type:  bool
      :value: False



   .. py:attribute:: dry_run
      :type:  bool
      :value: False



   .. py:attribute:: no_ast
      :type:  bool
      :value: False



   .. py:attribute:: complexity
      :type:  bool
      :value: False



   .. py:attribute:: patterns
      :type:  list[str] | None
      :value: None



   .. py:attribute:: verbose
      :type:  bool
      :value: False



.. py:function:: check(path = '.', *, fix = False, interactive = False, dry_run = False, no_ast = False, complexity = False, patterns = None, verbose = False)

   🔍 Check code for logging best practices with AST analysis by default.

   Examples:
     nicestlog check file.py                    # Basic linting + AST analysis
     nicestlog check file.py --fix              # Fix with AST transforms
     nicestlog check file.py --interactive      # Interactive mode
     nicestlog check file.py --dry-run --fix    # Preview fixes

   For advanced options, use: nicestlog tools check-advanced



.. py:class:: MigrateOptions

   Options for the migrate command.


   .. py:attribute:: path
      :type:  str
      :value: '.'



   .. py:attribute:: output
      :type:  str | None
      :value: None



   .. py:attribute:: dry_run
      :type:  bool
      :value: False



   .. py:attribute:: no_dry_run
      :type:  bool
      :value: False



   .. py:attribute:: type
      :type:  str
      :value: 'print-to-structlog'



   .. py:attribute:: no_ast
      :type:  bool
      :value: False



   .. py:attribute:: pattern
      :type:  str | None
      :value: None



   .. py:attribute:: interactive
      :type:  bool
      :value: False



   .. py:attribute:: verbose
      :type:  bool
      :value: False



   .. py:attribute:: check_imports
      :type:  bool
      :value: False



   .. py:attribute:: force
      :type:  bool
      :value: False



   .. py:attribute:: json_output
      :type:  bool
      :value: False



.. py:function:: migrate(path = '.', *, output = None, dry_run = False, no_dry_run = False, type = 'print-to-structlog', no_ast = False, pattern = None, interactive = False, verbose = False, check_imports = False, force = False, json = False)

   🔄 Analyze project and migrate code.

   Default behavior: Dry-run preview (safe, shows what would change)

   Examples:
      nicestlog migrate                                   # Dry-run preview of current project
      nicestlog migrate /path/to/project                  # Dry-run preview of specific project
      nicestlog migrate . --json                          # Agent analysis output
      nicestlog migrate . --no-dry-run                    # Actually apply changes
      nicestlog migrate . --no-dry-run --type logging-to-structlog  # Specific migration
      nicestlog migrate . --no-dry-run --interactive      # Interactive migration



.. py:function:: tools_demo(feature = None, *, all_features = False)

   🎬 Run interactive demos.


.. py:function:: run_dashboard_cmd(host = '127.0.0.1', port = 8080, *, debug = False)

   Run the web dashboard.


.. py:function:: run_journal_viewer(unit = None, lines = 50, *, follow = False, since = None, level = None)

   Run the journal viewer.


.. py:function:: run_log_reviewer(path_str, format_type = 'text', min_score = 70.0)

   Run the log reviewer.


.. py:function:: generate_service_cmd(service_name, exec_command, user = None, working_directory = None, output_file = None)

   Generate systemd service file.


.. py:function:: run_demos(feature = None, *, all_features = False)

   Run nicestlog feature demonstrations.


.. py:function:: print_demo_header(_title, _description)

   Print a formatted demo section header.


.. py:function:: run_basic_demo()

   Demonstrate basic nicestlog features.


.. py:function:: run_i18n_demo()

   Demonstrate internationalization features.


.. py:function:: run_pii_demo()

   Demonstrate PII scrubbing features.


.. py:function:: run_eliot_demo()

   Demonstrate Eliot integration.


.. py:function:: run_systemd_demo()

   Demonstrate systemd integration.


.. py:function:: run_async_demo()

   Demonstrate async logging.


.. py:function:: run_complete_demo()

   Demonstrate complete application example.


.. py:function:: run_lint_demo()

   Demonstrate linting functionality.


.. py:data:: MIGRATION_TYPES

.. py:function:: run_migrate_command(options, *, migration_type, force = False)

   Execute migration command with comprehensive AST integration.


.. py:function:: migrate_single_file(source, target, config, *, dry_run, _force)

   Migrate a single file using the appropriate handler.


.. py:function:: migrate_directory_recursive(source, target, config, *, dry_run, force)

   Migrate all Python files in a directory recursively.


.. py:function:: run_interactive_migration(transformer, source, _target, config, *, _dry_run)

   Run interactive migration using InteractiveTransformer.


.. py:function:: migrate_directory_with_handler(input_dir, output_dir, migration_handler, *, dry_run = True)

   Migrate Python files using a custom migration handler function.


.. py:function:: show_migration_report(result, *, dry_run)

   Display comprehensive migration results.


.. py:function:: main()

   Main entry point.


