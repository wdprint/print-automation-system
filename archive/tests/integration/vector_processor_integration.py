
def process_pdf_with_vector_thumbnails(order_pdf, print_pdf, output_path):
    """
    벡터 방식으로 썸네일을 삽입하는 개선된 프로세서
    기존 래스터 방식 대체용
    """
    from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
    
    try:
        # 설정
        thumbnail_positions = [
            (230, 234),  # 왼쪽
            (658, 228)   # 오른쪽
        ]
        thumbnail_size = (160, 250)  # 픽셀
        
        # 파일 읽기
        order_reader = PdfReader(order_pdf)
        if print_pdf:
            thumb_reader = PdfReader(print_pdf)
            thumb_page = thumb_reader.pages[0]
            
            # 스케일 계산
            orig_w = float(thumb_page.mediabox.width)
            orig_h = float(thumb_page.mediabox.height)
            target_w = thumbnail_size[0] * 0.75  # to points
            target_h = thumbnail_size[1] * 0.75
            scale = min(target_w / orig_w, target_h / orig_h)
        
        writer = PdfWriter()
        
        # 각 페이지 처리
        for page_num, base_page in enumerate(order_reader.pages):
            # 페이지 복사
            new_page = PageObject.create_blank_page(
                width=base_page.mediabox.width,
                height=base_page.mediabox.height
            )
            new_page.merge_page(base_page)
            
            # 썸네일 삽입 (print_pdf가 있을 때만)
            if print_pdf:
                for x, y in thumbnail_positions:
                    # 썸네일 복사 및 변환
                    thumb = thumb_reader.pages[0]
                    transform = Transformation().scale(
                        sx=scale, sy=scale
                    ).translate(tx=x, ty=y)
                    thumb.add_transformation(transform)
                    new_page.merge_page(thumb)
            
            writer.add_page(new_page)
        
        # 저장
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
