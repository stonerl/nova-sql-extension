/* LanguageClient wrapper for the bundled sqls language server. */

const SQL_SYNTAXES = [
  "sql-generic",
  "mysql",
  "mariadb",
  "postgresql",
  "tsql",
  "plsql",
  "sqlite",
  "bigquery",
  "flinksql",
  "hiveql",
  "n1ql",
  "redshift",
  "singlestore",
  "snowflake",
  "sparksql",
  "sqlpl",
  "trino",
];

const PREF_PREFIX = "stonerl.sql.";

class SqlsLanguageServer {
  constructor() {
    this.languageClient = null;
  }

  start() {
    if (this.languageClient) {
      return;
    }

    const binaryPath = this.configuredBinaryPath();
    if (!nova.fs.access(binaryPath, nova.fs.F_OK)) {
      console.error("sqls binary not found at:", binaryPath);
      return;
    }

    const serverOptions = {
      path: binaryPath,
      args: [],
    };

    const clientOptions = {
      syntaxes: SQL_SYNTAXES,
    };

    const client = new LanguageClient(
      "sqls",
      "SQL Language Server",
      serverOptions,
      clientOptions,
    );

    try {
      client.start();
      console.log("sqls language server started:", binaryPath);
      nova.subscriptions.add(client);
      this.languageClient = client;
    } catch (err) {
      console.error("Failed to start sqls language server:", err);
      if (nova.inDevMode()) {
        nova.workspace.showInformativeMessage(
          "The SQL language server could not be started. Check the Extension Console for details.",
        );
      }
    }
  }

  stop() {
    if (this.languageClient) {
      this.languageClient.stop();
      nova.subscriptions.remove(this.languageClient);
      this.languageClient = null;
      console.log("sqls language server stopped");
    }
  }

  restart() {
    this.stop();
    this.start();
  }

  configuredBinaryPath() {
    const customPath = nova.config.get(
      PREF_PREFIX + "sqls-binary-path",
      "string",
    );
    return customPath || nova.extension.path + "/Executables/sqls";
  }
}

exports.activate = function () {
  const server = new SqlsLanguageServer();

  // Respect the enable-language-server preference; start once per editor
  // opening like most Nova LSP extensions do (activation events already
  // gate on SQL syntaxes).
  if (nova.config.get(PREF_PREFIX + "enable-language-server")) {
    server.start();
  } else {
    console.log("SQL language server disabled by preference");
  }

  nova.config.onDidChange(PREF_PREFIX + "enable-language-server", (enabled) => {
    if (enabled) {
      server.start();
    } else {
      server.stop();
    }
  });

  nova.config.onDidChange(PREF_PREFIX + "sqls-binary-path", () => {
    if (nova.config.get(PREF_PREFIX + "enable-language-server")) {
      server.restart();
    }
  });

  nova.commands.register("restartLanguageServer", () => {
    server.restart();
  });

  nova.commands.register("showServerInfo", async () => {
    const enabled = nova.config.get(PREF_PREFIX + "enable-language-server");
    const path = server.configuredBinaryPath();
    const exists = nova.fs.access(path, nova.fs.F_OK);
    await nova.workspace.showInformativeMessage(
      [
        `Language server: ${enabled ? "enabled" : "disabled"}`,
        `Binary: ${path}`,
        exists ? "Binary found." : "Binary NOT found — check the path.",
      ].join("\n"),
    );
  });
};

exports.deactivate = function () {
  // LanguageClient is disposed via nova.subscriptions.
};
