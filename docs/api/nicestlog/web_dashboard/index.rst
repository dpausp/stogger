nicestlog.web_dashboard
=======================

.. py:module:: nicestlog.web_dashboard

.. autoapi-nested-parse::

   Simple Flask + HTMX web dashboard for live log viewing.

   No async bullshit, just good old Flask with HTMX for live updates.



Attributes
----------

.. autoapisummary::

   nicestlog.web_dashboard.FLASK_AVAILABLE
   nicestlog.web_dashboard.MAX_RECENT_LOGS
   nicestlog.web_dashboard.ONE_MINUTE_SECONDS
   nicestlog.web_dashboard.log_buffer
   nicestlog.web_dashboard.recent_logs
   nicestlog.web_dashboard.log_lock
   nicestlog.web_dashboard.DASHBOARD_HTML
   nicestlog.web_dashboard.LOG_ENTRY_TEMPLATE


Classes
-------

.. autoapisummary::

   nicestlog.web_dashboard.WebLogHandler


Functions
---------

.. autoapisummary::

   nicestlog.web_dashboard.create_dashboard_app
   nicestlog.web_dashboard.get_log_stats
   nicestlog.web_dashboard.setup_web_logging
   nicestlog.web_dashboard.run_dashboard
   nicestlog.web_dashboard.generate_demo_logs


Module Contents
---------------

.. py:data:: FLASK_AVAILABLE
   :value: True


.. py:data:: MAX_RECENT_LOGS
   :value: 500


.. py:data:: ONE_MINUTE_SECONDS
   :value: 60


.. py:data:: log_buffer
   :type:  queue.Queue[dict[str, Any]]

.. py:data:: recent_logs
   :type:  list[dict[str, Any]]
   :value: []


.. py:data:: log_lock

.. py:class:: WebLogHandler

   Handle logs for the web dashboard.


   .. py:attribute:: session_id


.. py:data:: DASHBOARD_HTML
   :value: Multiline-String

   .. raw:: html

      <details><summary>Show Value</summary>

   .. code-block:: python

      """
      <!DOCTYPE html>
      <html lang="en">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Nicestlog Dashboard</title>
          <script src="https://unpkg.com/htmx.org@1.9.10"></script>
          <style>
              body {
                  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                  background: #1a1a1a;
                  color: #e0e0e0;
                  margin: 0;
                  padding: 20px;
              }
              .header {
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  padding: 20px;
                  border-radius: 10px;
                  margin-bottom: 20px;
                  text-align: center;
              }
              .header h1 {
                  margin: 0;
                  color: white;
                  font-size: 2em;
              }
              .controls {
                  background: #2d2d2d;
                  padding: 15px;
                  border-radius: 8px;
                  margin-bottom: 20px;
                  display: flex;
                  gap: 10px;
                  align-items: center;
              }
              .log-container {
                  background: #2d2d2d;
                  border-radius: 8px;
                  padding: 20px;
                  max-height: 70vh;
                  overflow-y: auto;
                  border: 1px solid #444;
              }
              .log-entry {
                  margin-bottom: 10px;
                  padding: 10px;
                  border-left: 4px solid #666;
                  background: #333;
                  border-radius: 4px;
                  font-size: 14px;
                  line-height: 1.4;
              }
              .log-entry.debug { border-left-color: #888; }
              .log-entry.info { border-left-color: #4CAF50; }
              .log-entry.warning { border-left-color: #FF9800; }
              .log-entry.error { border-left-color: #f44336; }
              .log-entry.critical { border-left-color: #9C27B0; }
      
              .log-timestamp {
                  color: #888;
                  font-size: 12px;
              }
              .log-level {
                  display: inline-block;
                  padding: 2px 6px;
                  border-radius: 3px;
                  font-weight: bold;
                  font-size: 11px;
                  margin-right: 8px;
              }
              .log-level.debug { background: #666; color: white; }
              .log-level.info { background: #4CAF50; color: white; }
              .log-level.warning { background: #FF9800; color: white; }
              .log-level.error { background: #f44336; color: white; }
              .log-level.critical { background: #9C27B0; color: white; }
      
              .log-event {
                  color: #e0e0e0;
                  font-weight: bold;
                  margin-right: 10px;
              }
              .log-logger {
                  color: #64B5F6;
                  font-size: 12px;
                  margin-right: 10px;
              }
              .log-data {
                  color: #A5D6A7;
                  font-size: 12px;
                  margin-top: 5px;
              }
              .btn {
                  background: #667eea;
                  color: white;
                  border: none;
                  padding: 8px 16px;
                  border-radius: 4px;
                  cursor: pointer;
                  font-size: 14px;
              }
              .btn:hover {
                  background: #5a67d8;
              }
              .btn.danger {
                  background: #f44336;
              }
              .btn.danger:hover {
                  background: #d32f2f;
              }
              select {
                  background: #444;
                  color: white;
                  border: 1px solid #666;
                  padding: 8px;
                  border-radius: 4px;
              }
              .stats {
                  display: flex;
                  gap: 20px;
                  margin-bottom: 20px;
              }
              .stat-card {
                  background: #2d2d2d;
                  padding: 15px;
                  border-radius: 8px;
                  text-align: center;
                  flex: 1;
              }
              .stat-number {
                  font-size: 24px;
                  font-weight: bold;
                  color: #667eea;
              }
              .stat-label {
                  font-size: 12px;
                  color: #888;
                  margin-top: 5px;
              }
              .auto-scroll {
                  position: sticky;
                  bottom: 20px;
                  text-align: right;
                  margin-top: 10px;
              }
          </style>
      </head>
      <body>
          <div class="header">
              <h1>🚽 Nicestlog Dashboard</h1>
              <p>Live log monitoring with style!</p>
          </div>
      
          <div class="stats" id="stats" hx-get="/api/stats" hx-trigger="every 2s">
              <div class="stat-card">
                  <div class="stat-number">{{ stats.total_logs }}</div>
                  <div class="stat-label">Total Logs</div>
              </div>
              <div class="stat-card">
                  <div class="stat-number">{{ stats.error_count }}</div>
                  <div class="stat-label">Errors</div>
              </div>
              <div class="stat-card">
                  <div class="stat-number">{{ stats.warning_count }}</div>
                  <div class="stat-label">Warnings</div>
              </div>
              <div class="stat-card">
                  <div class="stat-number">{{ stats.logs_per_minute }}</div>
                  <div class="stat-label">Logs/min</div>
              </div>
          </div>
      
          <div class="controls">
              <button class="btn" hx-post="/api/clear" hx-target="#logs">Clear Logs</button>
              <select id="level-filter" hx-get="/api/logs" hx-target="#logs" hx-trigger="change">
                  <option value="">All Levels</option>
                  <option value="debug">Debug</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                  <option value="critical">Critical</option>
              </select>
              <label>
                  <input type="checkbox" id="auto-scroll" checked> Auto-scroll
              </label>
              <span style="margin-left: auto; color: #888;">
                  Live updates every 1s
              </span>
          </div>
      
          <div class="log-container">
              <div id="logs" hx-get="/api/logs" hx-trigger="every 1s">
                  <!-- Logs will be loaded here -->
              </div>
              <div class="auto-scroll">
                  <button class="btn" onclick="scrollToBottom()">📍 Scroll to Bottom</button>
              </div>
          </div>
      
          <script>
              function scrollToBottom() {
                  const container = document.querySelector('.log-container');
                  container.scrollTop = container.scrollHeight;
              }
      
              // Auto-scroll when new logs arrive
              document.body.addEventListener('htmx:afterSwap', function(evt) {
                  if (evt.detail.target.id === 'logs' && document.getElementById('auto-scroll').checked) {
                      setTimeout(scrollToBottom, 100);
                  }
              });
      
              // Initial scroll to bottom
              setTimeout(scrollToBottom, 500);
          </script>
      </body>
      </html>
      """

   .. raw:: html

      </details>



.. py:data:: LOG_ENTRY_TEMPLATE
   :value: Multiline-String

   .. raw:: html

      <details><summary>Show Value</summary>

   .. code-block:: python

      """
      <div class="log-entry {{ log.level }}">
          <span class="log-timestamp">{{ log.timestamp[:19] }}</span>
          <span class="log-level {{ log.level }}">{{ log.level.upper() }}</span>
          <span class="log-logger">[{{ log.logger }}]</span>
          <span class="log-event">{{ log.event }}</span>
          {% if log.data %}
          <div class="log-data">
              {% for key, value in log.data.items() %}
                  <span style="color: #81C784;">{{ key }}</span>=<span style="color: #F8BBD0;">{{ value }}</span>
              {% endfor %}
          </div>
          {% endif %}
      </div>
      """

   .. raw:: html

      </details>



.. py:function:: create_dashboard_app()

   Create the Flask dashboard app.


.. py:function:: get_log_stats()

   Calculate log statistics.


.. py:function:: setup_web_logging()

   Set up web logging integration.


.. py:function:: run_dashboard(host='127.0.0.1', port=8080, *, debug=False)

   Run the web dashboard.


.. py:function:: generate_demo_logs()

   Generate demo logs for testing.


