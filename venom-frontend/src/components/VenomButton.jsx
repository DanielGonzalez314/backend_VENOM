import { motion } from 'framer-motion';

const VenomButton = ({ children, onClick, variant = 'primary', className = '' }) => {
  const variants = {
    primary: "bg-white text-black hover:bg-gray-200",
    secondary: "bg-white/5 text-white border border-white/10 hover:bg-white/10",
    danger: "bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20"
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`px-6 py-2.5 rounded-xl font-bold transition-all duration-200 shadow-lg ${variants[variant]} ${className}`}
    >
      {children}
    </motion.button>
  );
};

export default VenomButton;