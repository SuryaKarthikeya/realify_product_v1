import { motion } from 'framer-motion';
import React from 'react';

const Skeleton = ({ 
  variant = 'rectangle', 
  width, 
  height, 
  className = '', 
  ...props 
}) => {
  const baseClasses = "bg-gray-200 dark:bg-slate-800 relative overflow-hidden";
  
  const variantClasses = {
    circular: "rounded-full",
    rectangle: "rounded-lg",
    text: "rounded h-4 w-full mb-2"
  };

  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={{ width, height }}
      {...props}
    >
      {/* Shimmer Effect */}
      <motion.div
        initial={{ x: '-100%' }}
        animate={{ x: '100%' }}
        transition={{ 
          repeat: Infinity, 
          duration: 1.5, 
          ease: "linear" 
        }}
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 dark:via-slate-700/30 to-transparent"
      />
    </div>
  );
};

export default Skeleton;
