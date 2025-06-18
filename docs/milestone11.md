## モデル変更
```text
DEFAULT_MODEL    = "all-mpnet-base-v2"
```
## 実行コマンドと理由

| フェーズ            | コマンド                                                                                                                                                                                        | 理由／目的                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **バックアップ (任意)** | `cp scripts/build_embeddings.py scripts/build_embeddings.backup.py`                                                                                                                         | 元スクリプトを残しておきたい場合。                                                                                                   |
| **旧ベクトル削除**     | `rm data/vectors.npy`<br>`rm data/docmap.json`                                                                                                                                              | MiniLM で生成した古いベクトルとマップを完全に排除し、ファイル名衝突や整合性崩壊を防ぐ。                                                                     |
| **新ベクトル生成**     | `bash\npython scripts/build_embeddings.py \\\n  --model all-mpnet-base-v2 \\\n  --batch 8 \\\n  --textdir data/texts \\\n  --out-vect data/vectors.npy \\\n  --out-map  data/docmap.json\n` | MPNet で埋め込みを作成。バッチサイズ8は M4/32 GB を想定した省メモリ設定。`vectors.npy` と `docmap.json` を **同じファイル名で再生成** することで、既存検索コードを修正せず切替え。 |
| **FAISS 再構築**   | `bash\npoetry run rfc-chronicle build-faiss \\\n  --vectors data/vectors.npy \\\n  --index  data/faiss_index.bin\n`                                                                         | 新ベクトルで高速検索インデックスを作成。`faiss_index.bin` が置き換わり、セマンティック検索が MPNet ベースになる。                                               |
| **動作確認**        | `bash\npoetry run rfc-chronicle semsearch \"OAuth 2.0\"\n`                                                                                                                                  | インデックスが正しく読めるか、結果が返るかをテスト。                                                                                          |


