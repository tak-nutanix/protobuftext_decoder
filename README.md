
# 概要
Nutanix ではプロセス間通信として gRPC が主に使用されており、オブジェクトは ProtocolBuffer でシリアライズされる。

ProtocolBuffer は本来、バイナリデータで表現されスキーマを介してそのデータ構造および意味を得るものであるが、一方、テキストで表現された形式も存在する。

バイナリデータについては `protoc --decode_raw` コマンドで構造化されたデータをテキストで得ることができる。ただしその意味合いについてはスキーマ(*.proto ファイル)を参照するしかない。

テキストでの表現では JSON にもにた、ただし区切りとなる記号や配列の表現が異なる構造化された書式で表現されるが、これはなまじ JSON に類似しているためそのままでは読みづらく、また大体において Pretty Print されていないため人が解釈するのに手間を要する。

Nutanix のログにはこのテキストで表現されたオブジェクトが記載される場合があり、ログ解析の場においてこの手間は馬鹿にならない。

このためテキストで表現された ProtocolBuffer のテキストでの書式を解釈し、より読みやすく一般的なツールで処理しやすい JSON に変換するのがこの protobuftext_decoder になる。

できるだけ簡単に持ち運び、利用ができるようにするため意図的にモジュールを構成せず、venv などの仕組みを使用せず、また Python 標準のモジュールしか使用しないようにしている。

## インストール

`protobuftext_decoder.py` およびそのほか .py ファイルを実行パスの通ったディレクトリにコピーする。

## 使い方

|コマンド | 用途 |
| --- | --- |
| protobuftext_decoder.py | 汎用の ProtocolBuffer デコード |
| alert_list_pb.py | logbay のログアーカイブに含まれる事のある alerts.txt ファイルの内容表示 |
| event_list_pb.py | logbay のログアーカイブに含まれる alert_events.txt ファイルの内容表示 |
| ngt_list.py | logbay のログアーカイブに含まれる nutanix_guest_tools_cli.txt ファイルの内容表示 |
| resiliency_status.py | zeus_config.txt からの Resiliency Status を抜き出し表示 |

- `protocol_buffer <filename>`

filename に記載された ProtocolBuffer のテキスト表現を読み込み、JSON で出力する。
なお、ファイル名を指定しない場合、標準入力から読み込まれるものと期待する。

- `protocol_buffer -r '<repeatkey1>,<repeatkey2>,...'`

JSONと異なり、ProtocolBuffer のテキスト表現では配列を明示的に指定する事がない。同じ階層で同じキーの異なるデータが列挙されることで配列を表現している。それが配列であるかはスキーマ(.proto)があれば自明となるが、.proto がないところで動作する protocol_buffer コマンドではその判別は難儀である。  
そこで、キーの名称に対してそれが配列であり同じキーが連続することを指定するのが -r オプションである。
-r では複数のキーを指定できるが、その場合は空白を入れず , で区切ること。


なお、protocol_buffer の本質はこれを import して想定されるデータごとに個別の Python スクリプトを用意することにある。ngt_list.py や resiliency_status.py はそうしたものになる。

そのほか .py については、logbay のログアーカイブを展開したディレクトリがカレントであることを前提に、適当に対象ファイルを探し、内容を表示する。




