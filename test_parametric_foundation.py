
import os
from pathlib import Path

# 今回作ったモジュールたちの読み込み
from services.font_engine.generator.profile_extractor import ProfileExtractor
from services.font_engine.generator.stroke_analyzer import StrokeAnalyzer
from services.pipeline.font_loader import FontLoader

def run_parametric_test():
    print("=" * 60)
    print("🚀 PR1: Parametric Foundation - 動作確認テストを開始します")
    print("=" * 60)

    # 1. テスト用フォントファイルの探索
    # ※環境に合わせてパスを調整してください（プロジェクト内にあるNoto SansなどのTTF）
    possible_paths = [
        Path("tests/fonts/NotoSans-Regular.ttf"),
        Path("tests/data/NotoSans-Regular.ttf"),
        Path("NotoSans-Regular.ttf")
    ]
    
    font_path = None
    for p in possible_paths:
        if p.exists():
            font_path = p
            break
            
    if not font_path:
        # 見つからない場合は、システムフォントやカレントディレクトリを探索するフォールバック
        print("⚠️ 規定のパスに NotoSans-Regular.ttf が見つかりません。")
        print("   プロジェクト内にある .ttf ファイルを探します...")
        ttf_files = list(Path(".").glob("**/*.ttf"))
        if ttf_files:
            font_path = ttf_files[0]
            print(f"🔍 見つかったフォントを使用します: {font_path}")
        else:
            print("❌ テスト用の .ttf フォントファイルがリポジトリ内に見つかりません。")
            print("   tests/fonts/ などの配下にフォントを配置するか、パスをスクリプトに指定してください。")
            return

    # 2. FontLoader でフォントを読み込む
    print(f"\n[STEP 1] フォントをロード中... 📂")
    loader = FontLoader()
    try:
        loaded_font = loader.load(font_path)
        print(f" └ ファミリー名: {loaded_font.family_name}")
        print(f" └ スタイル名  : {loaded_font.style_name}")
        print(f" └ UPM (Unit/Em): {loaded_font.upm}")
    except Exception as e:
        print(f"❌ フォントの読み込みに失敗しました: {e}")
        return

    # 3. StrokeAnalyzer で特定の文字（I）のストロークを解析
    print(f"\n[STEP 2] StrokeAnalyzer によるグリフ解析... 🩻")
    glyph_data = loader.extract_glyph(loaded_font, "I")
    if not glyph_data:
        print(" ⚠️ 'I' のグリフが抽出できなかったため、'A' で再試行します。")
        glyph_data = loader.extract_glyph(loaded_font, "A")
        
    if glyph_data:
        characteristics = StrokeAnalyzer.analyze_glyph(glyph_data)
        print(f" └ 推定された縦線の太さ (Stem Width): {characteristics.estimated_stem_width:.2f} px")
        print(f" └ 推定された横線の太さ (Bar Width) : {characteristics.estimated_crossbar_width:.2f} px")
        print(f" └ バウンディングボックス: X({characteristics.min_x} to {characteristics.max_x}), Y({characteristics.min_y} to {characteristics.max_y})")
    else:
        print(" ❌ 解析可能なグリフデータが取得できませんでした。")
        return

    # 4. ProfileExtractor で FontStyleProfile (DNA) を抽出
    print(f"\n[STEP 3] ProfileExtractor でフォントの DNA (Profile) を抽出... 🧬")
    profile = ProfileExtractor.extract_from_existing_font(loaded_font)
    
    print("-" * 40)
    print(f" 🌟 抽出された FontStyleProfile 結果 🌟")
    print(f"  ▪️ 逆算された Weight (100-900): {profile.weight:.1f}")
    print(f"  ▪️ スケール Width (50-200)   : {profile.width:.1f}")
    print(f"  ▪️ 傾き角度 Slant (度数)     : {profile.slant:.1f}")
    print(f"  ▪️ 縦横ストロークコントラスト : {profile.contrast:.2f}")
    print(f"  ▪️ 小文字高さ比率 (x-height)  : {profile.x_height_ratio:.2f}")
    print("-" * 40)
    print("\n🎉 PR1 基盤システムの結合テスト成功！正常に動作しています。")

if __name__ == "__main__":
    run_parametric_test()
