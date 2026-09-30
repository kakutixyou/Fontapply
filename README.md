# WebForge AI Desktop

フォント編集用のデスクトップアプリです。画面は React + Vite、デスクトップ機能は Electron、フォント処理/API は Python + FastAPI で構成する想定です。

## 起動方式

### 開発中

開発中は、次の3つを同時に動かします。

| プロセス | 役割 | 開発時の接続先 |
| --- | --- | --- |
| FastAPI | プロジェクト/グリフAPI | `http://127.0.0.1:8000` |
| Vite | React画面とホットリロード | `http://localhost:5173` |
| Electron | デスクトップウィンドウ | Viteの画面を表示 |

起動用batはこれらをまとめて立ち上げるための**開発用ランチャー**です。batを閉じてもプロセスが残る構成にしないこと、他の作業のPythonまで終了させるコマンドを使わないことが重要です。終了するときは、それぞれの起動したターミナルで `Ctrl+C` を押してください。

### バックエンドのIPアドレス設定

`0.0.0.0` はサーバーが「どのネットワークインターフェースで待ち受けるか」を指定する値です。クライアントが接続する宛先として `http://0.0.0.0:8000` を指定するものではありません。

- 同じPC上のブラウザー/Electronから使う場合: バックエンドは既定の `127.0.0.1:8000` で待ち受け、接続先も `http://127.0.0.1:8000` にします。
- 別のPCやコンテナから接続する場合: サーバー側で `FONT_API_HOST=0.0.0.0` を設定して待ち受け、クライアント側はサーバーの実際のLAN IP（例: `http://192.168.1.20:8000`）に接続します。

WindowsのコマンドプロンプトでLAN向けにバックエンドを起動する例:

```bat
set FONT_API_HOST=0.0.0.0
set FONT_API_PORT=8000
set FONT_API_CORS_ORIGINS=http://192.168.1.30:5173
python python_backend\main.py
```

この例では `192.168.1.30:5173` がフロントエンドを配信するPCのアドレスです。フロントエンドのAPI接続先も起動前に `VITE_FONT_API_BASE_URL` と `VITE_DESIGN_API_BASE_URL` に `http://192.168.1.20:8000` を設定してください。Electronから接続する場合は `FONT_API_BASE_URL` を同じ宛先に設定します。ホスト側ファイアウォールで必要な接続元だけを許可してください。`0.0.0.0` で待ち受けると、他の端末からも到達可能になるためです。

`FONT_API_HOST` の既定値は `127.0.0.1` です。LAN向け設定は開発用であり、インターネットへ直接公開しないでください。

### 配布するとき

配布版では、利用者にPythonやNode.jsを別途起動させず、Electronアプリが画面とPythonバックエンドを起動・終了管理する形を目指します。Pythonバックエンドは実行可能ファイル等として同梱し、Electronのアプリ終了時にバックエンドも停止させます。開発用batを配布版の起動方法として流用しないでください。

## 現在の起動・設定状況

このリポジトリの現在の作業ツリーでは、ルートにも `frontend` にも `package.json` がありません。Node依存関係のロックファイル、Pythonの `requirements.txt` も確認できていないため、現状のファイルだけではフロントエンド/Electronの依存関係を再現して起動できません。

共有された `package.json` の `dev` は Vite・Electron・Python を同時起動する設計ですが、起動bat側から `frontend` に移動してその `npm run dev` を呼ぶと、どちらの場所をプロジェクトルートとするかが食い違います。特に、ルート実行前提の `electron/...` と `python_backend/...` を参照するスクリプトを `frontend` で実行してはいけません。マニフェストを戻す際に、配置場所・Viteのroot・各コマンドの作業ディレクトリを揃えてください。

また、共有されたbatはPythonとfrontendを別ウィンドウで起動し、Electron起動部分はコメントアウトされています。package script側もPythonを起動する場合、batとscriptの両方からPythonを起動しないようにしてください。起動責任を「bat」か「npm script」のどちらか一方に決めます。

## 現在の実装範囲と注意点

- FastAPIは `python_backend/main.py` から起動し、`/health`、プロジェクトCRUD、`/api/glyphs` 系のルートを登録します。ローカルDBは `database/font_studio.db` に作成されます。初回起動時に `database` フォルダーがなくても作成します。
- FastAPIのfont export、import、analyticsルーターは現在無効化されています。画面に操作があっても、バックエンド側の対応が未完了の機能があります。
- Electronの `main.ts` は開発時にVite (`localhost:5173`) を表示し、フォントIPCは既定でFastAPI (`127.0.0.1:8000`) を呼び出します。接続先は `FONT_API_BASE_URL` で変更できます。
- ElectronのプロジェクトIPCやPythonステータスの一部はTODO/仮実装です。Electron画面から使うときは、各ボタンがFastAPIへ接続されているか個別に確認してください。
- `start.bat` は会話で共有されたファイルであり、現リポジトリ内にはありません。READMEの記述と手元のbatが異なる場合は、batの内容を確認してから使ってください。

## 開発を再開するときの確認順

1. `package.json` とNodeロックファイルをプロジェクト構成に合わせて復元し、`frontend` のVite設定・依存関係とElectronの起動スクリプトのルートを統一する。
2. Python依存関係を `requirements.txt` 等に固定し、新しい仮想環境からFastAPIを起動できるようにする。
3. FastAPIの `/health` を確認してから、プロジェクト一覧と `GET /api/glyphs/0041` を確認する。
4. Vite単体で画面を確認し、その後Electronを加えて、プロジェクト作成・グリフ読み込み・終了時の各プロセス停止を確認する。
5. 最後に、batを何度起動しても多重起動にならず、関係のないPythonプロセスを終了しないことを確認する。
