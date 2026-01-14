import HeroSection from '@/components/landing/HeroSection';
import ProblemSolution from '@/components/landing/ProblemSolution';
import FeaturesGrid from '@/components/landing/FeaturesGrid';
import HowItWorks from '@/components/landing/HowItWorks';
import TrustSection from '@/components/landing/TrustSection';
import DashboardPreview from '@/components/landing/DashboardPreview';
import FAQSection from '@/components/landing/FAQSection';
import BottomCTA from '@/components/landing/BottomCTA';
import { useTranslations } from 'next-intl';

export default function Home() {
  const t = useTranslations('HomePage');

  return (
    <main className="min-h-screen bg-slate-950 relative">
      <HeroSection />
      <ProblemSolution />
      <FeaturesGrid />
      <HowItWorks />
      <TrustSection />
      <DashboardPreview />
      <FAQSection />
      <BottomCTA />

      {/* Footer */}
      <footer id="contact" className="bg-slate-950 border-t border-slate-900 py-16">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div>
              <div className="flex items-center gap-2 mb-6">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white text-sm font-bold">◇</span>
                </div>
                <span className="text-lg font-bold text-white">ADC Platform</span>
              </div>
              <p className="text-slate-500 text-sm leading-relaxed">
                {t('footer.desc')}
              </p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-6">{t('footer.product')}</h4>
              <ul className="space-y-4 text-sm text-slate-400">
                <li><a href="#" className="hover:text-blue-400 transition-colors">{t('features.scoring')}</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">{t('features.evidence')}</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">{t('features.protocol')}</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-6">{t('footer.company')}</h4>
              <ul className="space-y-4 text-sm text-slate-400">
                <li><a href="#" className="hover:text-blue-400 transition-colors">About Us</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">Blog</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-6">{t('footer.contact')}</h4>
              <ul className="space-y-4 text-sm text-slate-400">
                <li>support@adc-platform.com</li>
                <li>+82 2-1234-5678</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-900 pt-8 text-center text-slate-600 text-sm">
            {t('footer.rights')}
          </div>
        </div>
      </footer>
    </main>
  );
}

