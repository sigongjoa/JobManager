import unittest
import os
import sys
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Portfolio, PortfolioLink, JobPosting, Resume, Schedule
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

class TestPortfolioManagement(unittest.TestCase):
    def setUp(self):
        """테스트 전에 실행될 설정"""
        # 테스트용 데이터베이스 설정
        self.engine = create_engine('sqlite:///test.db')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        """테스트 후에 실행될 정리 작업"""
        # 테스트 데이터베이스 정리
        self.db.close()
        self.engine.dispose()
        
        try:
            if os.path.exists("test.db"):
                os.remove("test.db")
        except OSError:
            pass

    def test_portfolio_creation(self):
        """포트폴리오 생성 테스트"""
        print("\n=== 포트폴리오 생성 테스트 ===")
        
        # 포트폴리오 생성
        portfolio = Portfolio(
            title="테스트 포트폴리오",
            description="테스트 설명"
        )
        self.db.add(portfolio)
        self.db.commit()
        
        # 포트폴리오가 생성되었는지 확인
        created_portfolio = self.db.query(Portfolio).filter_by(id=portfolio.id).first()
        self.assertIsNotNone(created_portfolio)
        self.assertEqual(created_portfolio.title, "테스트 포트폴리오")
        print("✓ 포트폴리오 생성 확인")

    def test_portfolio_links(self):
        """포트폴리오 링크 관리 테스트"""
        print("\n=== 포트폴리오 링크 관리 테스트 ===")
        
        # 포트폴리오 생성
        portfolio = Portfolio(
            title="테스트 포트폴리오",
            description="테스트 설명"
        )
        self.db.add(portfolio)
        self.db.commit()
        
        # 포트폴리오 링크 추가
        links = [
            PortfolioLink(
                portfolio_id=portfolio.id,
                title="GitHub",
                url="https://github.com/test",
                description="GitHub 저장소"
            ),
            PortfolioLink(
                portfolio_id=portfolio.id,
                title="데모",
                url="https://demo.test.com",
                description="프로젝트 데모"
            )
        ]
        for link in links:
            self.db.add(link)
        self.db.commit()
        
        # 링크가 추가되었는지 확인
        added_links = self.db.query(PortfolioLink).filter_by(portfolio_id=portfolio.id).all()
        self.assertEqual(len(added_links), 2)
        print("✓ 포트폴리오 링크 추가 확인")
        
        # 포트폴리오 삭제 시 링크도 함께 삭제되는지 확인
        self.db.delete(portfolio)
        self.db.commit()
        
        deleted_links = self.db.query(PortfolioLink).filter_by(portfolio_id=portfolio.id).all()
        self.assertEqual(len(deleted_links), 0)
        print("✓ 포트폴리오 삭제 시 링크도 함께 삭제 확인")

    def test_portfolio_update(self):
        """포트폴리오 수정 테스트"""
        print("\n=== 포트폴리오 수정 테스트 ===")
        
        # 포트폴리오 생성
        portfolio = Portfolio(
            title="테스트 포트폴리오",
            description="테스트 설명"
        )
        self.db.add(portfolio)
        self.db.commit()
        
        # 포트폴리오 수정
        new_title = "수정된 포트폴리오"
        new_description = "수정된 설명"
        portfolio.title = new_title
        portfolio.description = new_description
        self.db.commit()
        
        # 수정된 포트폴리오 확인
        updated_portfolio = self.db.query(Portfolio).filter_by(id=portfolio.id).first()
        self.assertEqual(updated_portfolio.title, new_title)
        self.assertEqual(updated_portfolio.description, new_description)
        print("✓ 포트폴리오 수정 확인")

    def test_portfolio_deletion(self):
        """포트폴리오 삭제 테스트"""
        print("\n=== 포트폴리오 삭제 테스트 ===")
        
        # 포트폴리오 생성
        portfolio = Portfolio(
            title="테스트 포트폴리오",
            description="테스트 설명"
        )
        self.db.add(portfolio)
        self.db.commit()
        
        # 포트폴리오 삭제
        portfolio_id = portfolio.id
        self.db.delete(portfolio)
        self.db.commit()
        
        # 포트폴리오가 삭제되었는지 확인
        deleted_portfolio = self.db.query(Portfolio).filter_by(id=portfolio_id).first()
        self.assertIsNone(deleted_portfolio)
        print("✓ 포트폴리오 삭제 확인")

if __name__ == '__main__':
    unittest.main(verbosity=2) 