import os
import numpy as np
import faiss
import pytest
from pathlib import Path

# テスト用ユーティリティ: 一時ディレクトリにダミーベクトルファイルを作成
@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    # テスト用 vectors.npy を作成
    vectors = np.random.random((10, 64)).astype('float32')
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    np.save(str(data_dir / "vectors.npy"), vectors)
    # テスト実行時の作業ディレクトリを一時ディレクトリに変更
    monkeypatch.chdir(tmp_path)
    return data_dir

# スクリプトへのパス取得
def get_script_path():
    return Path(__file__).parent.parent / "scripts" / "build_faiss_index.py"


def test_fresh_build_creates_index_file(temp_data_dir):
    index_path = temp_data_dir / "faiss_index.bin"
    script = get_script_path()
    # 全量ビルドを実行
    os.system(f"python3 {script} -v data/vectors.npy -i data/faiss_index.bin")
    # ファイル生成の確認
    assert index_path.exists(), "インデックスファイルが作成されていません"
    # インデックスの次元と件数チェック
    idx = faiss.read_index(str(index_path))
    assert isinstance(idx, faiss.IndexFlatL2)
    assert idx.ntotal == 10, f"期待件数 10, 実際 {idx.ntotal}"


def test_update_mode_increases_count(temp_data_dir):
    index_path = temp_data_dir / "faiss_index.bin"
    script = get_script_path()
    # 初回全量ビルド
    os.system(f"python3 {script} -v data/vectors.npy -i data/faiss_index.bin")
    # 差分用ベクトルを保存
    vectors2 = np.random.random((5, 64)).astype('float32')
    np.save(str(temp_data_dir / "vectors2.npy"), vectors2)
    # update モードで追加
    os.system(f"python3 {script} -v data/vectors2.npy -i data/faiss_index.bin -u")
    # インデックス件数が増えていることを確認
    idx = faiss.read_index(str(index_path))
    assert idx.ntotal == 15, f"期待件数 15, 実際 {idx.ntotal}"


def test_ivf_build_creates_ivf_index(temp_data_dir):
    index_path = temp_data_dir / "faiss_index.bin"
    script = get_script_path()
    # IVF 全量ビルドを実行
    os.system(f"python3 {script} -v data/vectors.npy -i data/faiss_index.bin -t ivf")
    # ファイル生成の確認
    assert index_path.exists(), "IVF インデックスファイルが作成されていません"
    # インデックスの型と件数チェック
    idx = faiss.read_index(str(index_path))
    assert isinstance(idx, faiss.IndexIVFFlat), f"期待型 IndexIVFFlat, 実際 {type(idx)}"
    assert idx.ntotal == 10, f"期待件数 10, 実際 {idx.ntotal}"
    # IVF インデックスは train 済みであること
    assert idx.is_trained, "IVF インデックスが train されていません"


def test_hnsw_build_creates_hnsw_index(temp_data_dir):
    index_path = temp_data_dir / "faiss_index.bin"
    script = get_script_path()
    # HNSW 全量ビルドを実行
    os.system(f"python3 {script} -v data/vectors.npy -i data/faiss_index.bin -t hnsw")
    # ファイル生成の確認
    assert index_path.exists(), "HNSW インデックスファイルが作成されていません"
    # インデックスの型と件数チェック
    idx = faiss.read_index(str(index_path))
    assert isinstance(idx, faiss.IndexHNSWFlat), f"期待型 IndexHNSWFlat, 実際 {type(idx)}"
    assert idx.ntotal == 10, f"期待件数 10, 実際 {idx.ntotal}"
