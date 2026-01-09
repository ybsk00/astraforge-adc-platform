import Link from 'next/link';
import { useTranslations } from 'next-intl';
import Interactive3DCell from '@/components/ui/Interactive3DCell';
import { Beaker, BookOpen, Zap, TrendingUp, Shield, Globe } from 'lucide-react';

export default function Home() {
  const t = useTranslations('HomePage');

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-lg border-b border-slate-800">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-bold">◇</span>
            </div>
            <span className="text-white font-bold">ADC Platform</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">서비스 소개</a>
            <a href="#interface" className="hover:text-white transition-colors">기능</a>
            <a href="#contact" className="hover:text-white transition-colors">솔루션</a>
          </div>
          <Link
            href="/login"
            className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            로그인
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="relative z-10">
              <div className="inline-block px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-6">
                AI Drug Discovery Platform
              </div>
              <h1 className="text-5xl lg:text-6xl font-bold text-white leading-tight mb-2">
                Accelerating
              </h1>
              <h1 className="text-5xl lg:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400 leading-tight mb-6">
                Next-Gen ADC<br />Discovery
              </h1>
              <p className="text-lg text-slate-400 mb-8 max-w-lg leading-relaxed">
                최첨단 AI 알고리즘으로 항체-약물 접합체(ADC)의 설계를 최적화하고, 연구 데이터를 빠르게 분석하여 신약 개발을 가속화하세요.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  href="/login"
                  className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition-all shadow-lg shadow-blue-600/25"
                >
                  시작하기
                </Link>
                <button className="px-8 py-4 bg-slate-800/50 hover:bg-slate-800 text-white font-semibold rounded-lg border border-slate-700 transition-all flex items-center gap-2">
                  데모 영상 보기
                </button>
              </div>
              <div className="mt-10 flex items-center gap-6 text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  FDA Data Compliant
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  Enterprise Security
                </div>
              </div>
            </div>

            {/* Hero Visual */}
            <div className="relative z-10 lg:h-[550px] flex items-center justify-center">
              <Interactive3DCell />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-slate-900/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-sm text-blue-400 font-medium uppercase tracking-wider mb-3">FEATURES</h2>
            <h3 className="text-3xl font-bold text-white mb-4">Advanced Tools for Researchers</h3>
            <p className="text-slate-400 max-w-2xl mx-auto">
              ADC 개발 과정에서 필요로 하는 다양한 분석 솔루션을 제공하며, 이를 쉽고 빠르게 해석하실 수 있도록 지원합니다.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-slate-800/30 border border-slate-800 rounded-2xl p-8 hover:border-slate-700 transition-colors group">
              <div className="w-14 h-14 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-400 mb-6 group-hover:bg-blue-500/20 transition-colors">
                <Beaker className="w-7 h-7" />
              </div>
              <h4 className="text-xl font-bold text-white mb-3">Smart Candidate Scoring</h4>
              <p className="text-slate-400 leading-relaxed text-sm">
                AI 기반 약물 후보 물질 분석: 다차원척도로 새로운 활성 물질 및 부작용 예측하여 효율성을 극대화합니다.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-slate-800/30 border border-slate-800 rounded-2xl p-8 hover:border-slate-700 transition-colors group">
              <div className="w-14 h-14 bg-purple-500/10 rounded-xl flex items-center justify-center text-purple-400 mb-6 group-hover:bg-purple-500/20 transition-colors">
                <BookOpen className="w-7 h-7" />
              </div>
              <h4 className="text-xl font-bold text-white mb-3">Global Literature Indexing</h4>
              <p className="text-slate-400 leading-relaxed text-sm">
                수백만 건 논문 정보 실시간 분석: 본 사이트의 머신러닝 모델은 해당 사이트 이외에서 참고한 논문들까지도 모두 수집합니다.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-slate-800/30 border border-slate-800 rounded-2xl p-8 hover:border-slate-700 transition-colors group">
              <div className="w-14 h-14 bg-green-500/10 rounded-xl flex items-center justify-center text-green-400 mb-6 group-hover:bg-green-500/20 transition-colors">
                <Zap className="w-7 h-7" />
              </div>
              <h4 className="text-xl font-bold text-white mb-3">Automated Protocol Gen</h4>
              <p className="text-slate-400 leading-relaxed text-sm">
                프로토콜 초안의 표준 자동 생성: 다수의 기존논문에서 검증된 프로토콜 참조, 실험 조건 개인화 기반 프로토콜 구성을 지원합니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* System Interface Section */}
      <section id="interface" className="py-24 bg-slate-950">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white mb-4">System Interface</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              직관적인 인터페이스를 통해 복잡한 데이터를 손쉽게 분석하고, 연구 인사이트를 한눈에 파악하세요.
            </p>
          </div>

          <div className="relative max-w-6xl mx-auto">
            {/* Glow effect */}
            <div className="absolute inset-0 bg-blue-500/10 blur-3xl rounded-full opacity-30"></div>

            {/* Dashboard Preview */}
            <div className="relative bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
              <div className="p-6 md:p-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Left Panel - Chart */}
                  <div className="md:col-span-2 bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                    <div className="flex items-center justify-between mb-6">
                      <h4 className="text-white font-medium">Binding Affinity Distribution</h4>
                      <span className="text-xs text-slate-400">Last 30 days</span>
                    </div>
                    {/* Mock Bar Chart */}
                    <div className="flex items-end gap-3 h-40">
                      <div className="flex-1 flex flex-col gap-1">
                        <div className="h-[30%] bg-blue-600/30 rounded-t"></div>
                        <span className="text-xs text-slate-500 text-center">nM</span>
                      </div>
                      <div className="flex-1 flex flex-col gap-1">
                        <div className="h-[50%] bg-blue-600/50 rounded-t"></div>
                        <span className="text-xs text-slate-500 text-center"></span>
                      </div>
                      <div className="flex-1 flex flex-col gap-1">
                        <div className="h-[70%] bg-blue-600/70 rounded-t"></div>
                        <span className="text-xs text-slate-500 text-center"></span>
                      </div>
                      <div className="flex-1 flex flex-col gap-1">
                        <div className="h-[90%] bg-blue-600 rounded-t"></div>
                        <span className="text-xs text-slate-500 text-center">pM</span>
                      </div>
                      <div className="flex-1 flex flex-col gap-1">
                        <div className="h-[60%] bg-blue-600/60 rounded-t"></div>
                        <span className="text-xs text-slate-500 text-center"></span>
                      </div>
                    </div>

                    {/* Mock Records */}
                    <div className="mt-6 space-y-2">
                      <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                        <span className="text-sm text-slate-300">ADC-2024-V1</span>
                        <span className="text-sm text-green-400">95.2%</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                        <span className="text-sm text-slate-300">ADC-2024-V2</span>
                        <span className="text-sm text-blue-400">88.1%</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                        <span className="text-sm text-slate-300">ADC-REF-01</span>
                        <span className="text-sm text-yellow-400">72.5%</span>
                      </div>
                    </div>
                  </div>

                  {/* Right Panel - Live Protocols */}
                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                    <h4 className="text-white font-medium mb-4">Live Protocols</h4>
                    <div className="space-y-4">
                      <div className="p-3 bg-gradient-to-r from-green-500/10 to-transparent border-l-2 border-green-500 rounded-r">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="w-2 h-2 rounded-full bg-green-500"></span>
                          <span className="text-sm text-white">Synthesis A</span>
                        </div>
                        <span className="text-xs text-slate-400">Running • 45% complete</span>
                      </div>
                      <div className="p-3 bg-gradient-to-r from-blue-500/10 to-transparent border-l-2 border-blue-500 rounded-r">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                          <span className="text-sm text-white">Toxicity Test</span>
                        </div>
                        <span className="text-xs text-slate-400">Pending • Queue #2</span>
                      </div>
                      <div className="p-3 bg-gradient-to-r from-purple-500/10 to-transparent border-l-2 border-purple-500 rounded-r">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                          <span className="text-sm text-white">Stability Assay</span>
                        </div>
                        <span className="text-xs text-slate-400">Scheduled • Tomorrow</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

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
                Empowering scientists with AI-driven insights for antibody-drug conjugate discovery.
              </p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-6">Product</h4>
              <ul className="space-y-4 text-sm text-slate-400">
                <li><a href="#" className="hover:text-blue-400 transition-colors">AI 후보 물질 스코어</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">문헌 데이터</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">프로토콜 자동화</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-6">Company</h4>
              <ul className="space-y-4 text-sm text-slate-400">
                <li><a href="#" className="hover:text-blue-400 transition-colors">회사 소개</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">채용</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">블로그</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-6">Contact</h4>
              <ul className="space-y-4 text-sm text-slate-400">
                <li>support@adc-platform.com</li>
                <li>+82 2-1234-5678</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-900 pt-8 text-center text-slate-600 text-sm">
            © 2024 ADC Platform Inc. All rights reserved.
          </div>
        </div>
      </footer>
    </main>
  );
}
