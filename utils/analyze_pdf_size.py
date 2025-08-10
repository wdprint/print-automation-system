"""PDF 파일 크기 차이 분석"""
import fitz
import os

def analyze_pdf(path, name):
    """PDF 파일 분석"""
    print(f"\n=== {name} 분석 ===")
    print(f"파일: {os.path.basename(path)}")
    print(f"크기: {os.path.getsize(path)/(1024*1024):.2f}MB")
    
    doc = fitz.open(path)
    print(f"페이지 수: {len(doc)}")
    
    total_images = 0
    for i, page in enumerate(doc):
        images = page.get_images()
        print(f"\n페이지 {i+1}:")
        print(f"  크기: {page.rect.width:.1f} x {page.rect.height:.1f}")
        print(f"  회전: {page.rotation}도")
        print(f"  이미지 수: {len(images)}")
        
        # 이미지 정보
        for img_idx, img in enumerate(images):
            xref = img[0]
            img_dict = doc.extract_image(xref)
            if img_dict:
                print(f"    이미지 {img_idx+1}: {img_dict['width']}x{img_dict['height']}, {len(img_dict['image'])/1024:.1f}KB")
        
        total_images += len(images)
    
    print(f"\n총 이미지 수: {total_images}")
    doc.close()
    return total_images

# 두 파일 분석
path1 = r"C:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845_완료_2.pdf"
path2 = r"C:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\이진성-작업의뢰서(25년8월) - 복사본 (3)_완료.pdf"

if os.path.exists(path1):
    analyze_pdf(path1, "작은 파일 (4MB)")
else:
    print(f"파일1 없음: {path1}")

if os.path.exists(path2):
    analyze_pdf(path2, "큰 파일 (15MB)")
else:
    print(f"파일2 없음: {path2}")

# 원본 의뢰서도 확인
original = r"C:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\이진성-작업의뢰서(25년8월).pdf"
if os.path.exists(original):
    print("\n" + "="*50)
    analyze_pdf(original, "원본 의뢰서")