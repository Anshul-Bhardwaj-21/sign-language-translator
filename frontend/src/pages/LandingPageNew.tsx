import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { GradientHeading } from '../components/ui/GradientHeading';
import { GlowButton } from '../components/ui/GlowButton';
import { GlassCard } from '../components/ui/GlassCard';
import { Video, Mic, MessageSquare, Accessibility, Zap, Shield } from 'lucide-react';

export default function LandingPageNew() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Video className="w-8 h-8" />,
      title: 'Real-time Sign Recognition',
      description: 'Advanced AI detects and interprets sign language gestures instantly',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: <Mic className="w-8 h-8" />,
      title: 'Voice Output',
      description: 'Natural text-to-speech converts captions to clear audio',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: <MessageSquare className="w-8 h-8" />,
      title: 'Live Captions',
      description: 'Real-time captions with confidence scores and word history',
      color: 'from-green-500 to-emerald-500',
    },
    {
      icon: <Accessibility className="w-8 h-8" />,
      title: 'Accessibility First',
      description: 'WCAG AA compliant with keyboard navigation and screen reader support',
      color: 'from-orange-500 to-red-500',
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: 'Lightning Fast',
      description: 'Sub-100ms latency for seamless real-time communication',
      color: 'from-yellow-500 to-orange-500',
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: 'Privacy Focused',
      description: 'Peer-to-peer video streams, no data stored on servers',
      color: 'from-indigo-500 to-purple-500',
    },
  ];

  return (
    <div className="min-h-screen overflow-hidden">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4 py-20">
        {/* Animated background */}
        <div className="absolute inset-0 overflow-hidden">
          <motion.div
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
          <motion.div
            className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"
            animate={{
              scale: [1.2, 1, 1.2],
              opacity: [0.5, 0.3, 0.5],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <GradientHeading level={1} className="mb-6">
              Breaking Communication Barriers
            </GradientHeading>
            
            <motion.p
              className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              Real-time sign language interpretation powered by AI. 
              Connect, communicate, and collaborate without barriers.
            </motion.p>

            <motion.div
              className="flex flex-col sm:flex-row gap-4 justify-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <GlowButton
                size="lg"
                onClick={() => navigate('/login')}
                icon={<Video className="w-5 h-5" />}
              >
                Get Started
              </GlowButton>
              <GlowButton
                size="lg"
                variant="secondary"
                onClick={() => {
                  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Learn More
              </GlowButton>
            </motion.div>
          </motion.div>

          {/* Demo Video Placeholder */}
          <motion.div
            className="mt-20"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            <GlassCard className="p-2">
              <div className="aspect-video bg-gradient-to-br from-blue-900/50 to-purple-900/50 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <Video className="w-20 h-20 mx-auto mb-4 text-blue-400" />
                  <p className="text-gray-400">Demo Video Coming Soon</p>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <GradientHeading level={2} className="mb-4">
              Powerful Features
            </GradientHeading>
            <p className="text-xl text-gray-400">
              Everything you need for seamless sign language communication
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <GlassCard hover glow className="p-6 h-full">
                  <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <GlassCard className="p-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
              >
                <div className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-2">
                  &lt;100ms
                </div>
                <div className="text-gray-400">Average Latency</div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <div className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                  95%+
                </div>
                <div className="text-gray-400">Recognition Accuracy</div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <div className="text-5xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent mb-2">
                  24/7
                </div>
                <div className="text-gray-400">Always Available</div>
              </motion.div>
            </div>
          </GlassCard>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <GradientHeading level={2} className="mb-6">
              Ready to Get Started?
            </GradientHeading>
            <p className="text-xl text-gray-400 mb-8">
              Join thousands of users breaking communication barriers every day
            </p>
            <GlowButton
              size="lg"
              onClick={() => navigate('/dashboard')}
              icon={<Video className="w-5 h-5" />}
            >
              Launch SignBridge Now
            </GlowButton>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-8 px-4 border-t border-white/10">
        <div className="max-w-7xl mx-auto text-center text-gray-500">
          <p>© 2026 SignBridge. Breaking barriers, building connections.</p>
        </div>
      </footer>
    </div>
  );
}
